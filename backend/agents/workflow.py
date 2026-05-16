from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.nodes import (
    detect_intent,
    security_validation,
    router_agent,
    retrieve_pinecone,
    retrieve_sql,
    generate_response
)

def build_workflow():
    workflow = StateGraph(AgentState)

    # Add nodes — names must NOT clash with AgentState field names
    workflow.add_node("intent_node", detect_intent)
    workflow.add_node("security_node", security_validation)
    workflow.add_node("router_node", router_agent)
    workflow.add_node("pinecone_node", retrieve_pinecone)
    workflow.add_node("sql_node", retrieve_sql)
    workflow.add_node("generator_node", generate_response)

    # Entry point
    workflow.set_entry_point("intent_node")

    # Linear flow up to the router
    workflow.add_edge("intent_node", "security_node")
    workflow.add_edge("security_node", "router_node")

    # Conditional routing after router decision
    def route_decision(state: AgentState):
        route = state.get("datasource_route")
        if route == "DENY":
            return "generator_node"
        elif route == "SQL":
            return "sql_node"
        elif route == "MULTI":
            return "pinecone_node"  # MULTI: pinecone first, then SQL
        else:
            return "pinecone_node"  # PINECONE or default

    workflow.add_conditional_edges(
        "router_node",
        route_decision,
        {
            "pinecone_node": "pinecone_node",
            "sql_node": "sql_node",
            "generator_node": "generator_node"
        }
    )

    # After pinecone: if MULTI, also run SQL; otherwise go to generator
    def after_pinecone(state: AgentState):
        if state.get("datasource_route") == "MULTI":
            return "sql_node"
        return "generator_node"

    workflow.add_conditional_edges(
        "pinecone_node",
        after_pinecone,
        {
            "sql_node": "sql_node",
            "generator_node": "generator_node"
        }
    )

    workflow.add_edge("sql_node", "generator_node")
    workflow.add_edge("generator_node", END)

    return workflow.compile()

app_workflow = build_workflow()

def run_agent(query: str, user_roles: list, user_id: int) -> AgentState:
    initial_state = AgentState(
        query=query,
        user_roles=user_roles,
        user_id=user_id,
        intent=None,
        is_sensitive=False,
        datasource_route=None,
        retrieved_context=[],
        sql_result=None,
        final_response="",
        confidence_score=0.0,
        citations=[],
        trace_logs=[]
    )
    return app_workflow.invoke(initial_state)
