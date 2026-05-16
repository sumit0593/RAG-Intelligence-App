from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.database.config import get_db
from backend.database import models
from backend.security.auth import get_current_active_user
from backend.agents.workflow import run_agent

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    confidence_score: float
    citations: List[Dict[str, Any]]
    trace_logs: List[str]

@router.post("/query", response_model=ChatResponse)
def query_agent(request: ChatRequest, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Log query
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="QUERY",
        target=request.query,
        status="PENDING"
    )
    db.add(audit_log)
    db.commit()

    try:
        user_roles = [current_user.role.name]
        result_state = run_agent(query=request.query, user_roles=user_roles, user_id=current_user.id)
        
        audit_log.status = "SUCCESS"
        db.commit()
        
        return ChatResponse(
            response=result_state["final_response"],
            confidence_score=result_state["confidence_score"],
            citations=result_state["citations"],
            trace_logs=result_state["trace_logs"]
        )
    except Exception as e:
        audit_log.status = f"FAILED: {e}"
        db.commit()
        raise e
