import os
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.agents.state import AgentState
from backend.retrieval.pinecone_store import EnterpriseRetriever
from backend.database.config import SessionLocal
from backend.database import models
from sqlalchemy import text

SENSITIVE_KEYWORDS = ["salary", "financial", "security incident", "compliance violation", "performance"]

def _get_llm():
    """Lazily initialize the LLM so the API key is read at request time."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY", "")
    )

def _get_retriever():
    """Lazily initialize retriever so Pinecone key is read at request time."""
    return EnterpriseRetriever()

def detect_intent(state: AgentState) -> AgentState:
    query = state["query"].lower()
    state["trace_logs"].append("Detecting intent...")

    state["is_sensitive"] = any(k in query for k in SENSITIVE_KEYWORDS)
    if state["is_sensitive"]:
        state["trace_logs"].append(f"Sensitivity detected: {state['is_sensitive']}")

    return state

def security_validation(state: AgentState) -> AgentState:
    state["trace_logs"].append("Performing Security Validation...")
    if state["is_sensitive"] and not any(r in state["user_roles"] for r in ["ADMIN", "HR", "FINANCE", "SECURITY"]):
        state["trace_logs"].append("Security Validation FAILED. Unauthorized.")
        state["datasource_route"] = "DENY"

        db = SessionLocal()
        try:
            sec_log = models.SecurityLog(
                user_id=state["user_id"],
                action="BLOCKED_SENSITIVE_QUERY",
                reason=f"Attempted to query: {state['query']} without sufficient roles."
            )
            db.add(sec_log)
            db.commit()
        finally:
            db.close()
    return state

def router_agent(state: AgentState) -> AgentState:
    if state.get("datasource_route") == "DENY":
        return state

    state["trace_logs"].append("Router Agent deciding path...")
    llm = _get_llm()
    prompt = f"""You are a query router. Given the query below, reply with ONLY one word:
PINECONE - for documents, policies, reports, text-based content.
SQL      - for structured data: employees, salaries, financial figures, tables.
MULTI    - requires both documents AND database records.

Query: {state['query']}
Reply with one word only:"""

    response = llm.invoke(prompt)
    route = response.content.strip().upper().split()[0]

    if route not in ["PINECONE", "SQL", "MULTI"]:
        route = "PINECONE"  # fallback

    state["datasource_route"] = route
    state["trace_logs"].append(f"Router Decision: {route}")
    return state

def retrieve_pinecone(state: AgentState) -> AgentState:
    if state.get("datasource_route") in ["PINECONE", "MULTI"]:
        state["trace_logs"].append(f"Retrieving from Pinecone for roles: {state['user_roles']}...")
        retriever = _get_retriever()
        results = retriever.hybrid_search(
            query=state["query"],
            allowed_roles=state["user_roles"],
            top_k=3
        )
        state["retrieved_context"].extend(results)
        state["trace_logs"].append(f"Retrieved {len(results)} chunks from Pinecone.")
    return state

def retrieve_sql(state: AgentState) -> AgentState:
    if state.get("datasource_route") in ["SQL", "MULTI"]:
        state["trace_logs"].append("Executing SQL Retrieval Agent...")
        llm = _get_llm()
        prompt = f"""Generate a read-only PostgreSQL SELECT query for the request below.
Return ONLY the SQL. No markdown, no explanation.
Available tables:
  employees (name, department, role, salary, performance_rating)
  financial_reports (quarter, year, revenue, expenses, status)

Request: {state['query']}"""

        response = llm.invoke(prompt)
        sql_query = response.content.strip().replace("```sql", "").replace("```", "").strip()

        # Block destructive statements
        blocked = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE"]
        if any(word in sql_query.upper() for word in blocked):
            state["sql_result"] = "Error: Unsafe SQL blocked by security policy."
            state["trace_logs"].append("SQL Agent blocked unsafe query.")
            return state

        state["trace_logs"].append(f"Generated SQL: {sql_query}")

        db = SessionLocal()
        try:
            result = db.execute(text(sql_query))
            rows = result.fetchall()
            state["sql_result"] = str(rows)
            state["trace_logs"].append(f"SQL successful. {len(rows)} rows returned.")
        except Exception as e:
            state["sql_result"] = f"SQL Execution Error: {e}"
            state["trace_logs"].append(f"SQL execution failed: {e}")
        finally:
            db.close()

    return state

def generate_response(state: AgentState) -> AgentState:
    if state.get("datasource_route") == "DENY":
        state["final_response"] = "Access denied. You do not have permission to access this information."
        state["confidence_score"] = 0.0
        state["citations"] = []
        return state

    state["trace_logs"].append("Generating grounded response...")
    llm = _get_llm()

    context_str = ""
    citations = []

    if state.get("retrieved_context"):
        context_str += "--- Document Context ---\n"
        for i, doc in enumerate(state["retrieved_context"]):
            context_str += f"[Doc {i + 1}]: {doc['text']}\n"
            citations.append({
                "source": doc["metadata"].get("filename", "Unknown"),
                "chunk": doc["chunk_id"],
                "score": doc["score"],
                "dense_score": doc.get("dense_score", 0.0),
                "bm25_score": doc.get("bm25_score", 0.0)
            })

    if state.get("sql_result"):
        context_str += f"--- Database Context ---\n{state['sql_result']}\n"
        citations.append({
            "source": "PostgreSQL Database",
            "chunk": "SQL Query Result",
            "score": 1.0
        })

    if not context_str.strip():
        state["final_response"] = "I could not find verified information in the authorized enterprise sources."
        state["confidence_score"] = 0.0
        state["citations"] = []
        return state

    prompt = f"""Answer the user's query strictly based on the provided context.
If the answer is not in the context, say exactly: "I could not find verified information in the authorized enterprise sources."
Never invent or guess information.

Context:
{context_str}

User Query: {state['query']}"""

    response = llm.invoke(prompt)
    state["final_response"] = response.content

    # Confidence score: weighted combination of similarity + DB presence + grounding check
    avg_sim = 0.0
    if state.get("retrieved_context"):
        avg_sim = sum(d.get("score", 0) for d in state["retrieved_context"]) / len(state["retrieved_context"])

    has_db = 1.0 if state.get("sql_result") and "Error" not in state.get("sql_result", "") else 0.0
    grounded = 0.0 if "I could not find verified information" in state["final_response"] else 1.0
    citation_coverage = min(len(citations) / 3.0, 1.0)  # normalize to max 3 sources

    # Formula: retrieval_sim(0.4) + db_presence(0.2) + grounding(0.3) + citation(0.1)
    score = (avg_sim * 0.4) + (has_db * 0.2) + (grounded * 0.3) + (citation_coverage * 0.1)
    state["confidence_score"] = round(score, 2)
    state["citations"] = citations
    state["trace_logs"].append(f"Response generated. Confidence: {state['confidence_score']}")

    return state
