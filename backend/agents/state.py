from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    query: str
    user_roles: List[str]
    user_id: int
    intent: Optional[str]
    is_sensitive: bool
    datasource_route: Optional[str] # "PINECONE", "SQL", "MULTI", "NONE"
    retrieved_context: List[Dict[str, Any]]
    sql_result: Optional[str]
    final_response: str
    confidence_score: float
    citations: List[Dict[str, Any]]
    trace_logs: List[str]
