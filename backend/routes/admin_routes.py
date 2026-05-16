from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from backend.database.config import get_db
from backend.database import models
from backend.security.auth import require_role, get_current_active_user
from backend.ingestion.loader import load_document
from backend.ingestion.chunker import DocumentChunker
from backend.retrieval.pinecone_store import EnterpriseRetriever
import os
import shutil

router = APIRouter()

retriever = EnterpriseRetriever()

def process_and_index_document(file_path: str, metadata: dict, db: Session):
    try:
        text = load_document(file_path)
        chunker = DocumentChunker()
        chunks = chunker.chunk_document(text, metadata)
        retriever.index_documents(chunks)
        # Update db document status or log
    except Exception as e:
        print(f"Error indexing document {file_path}: {e}")

@router.post("/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    classification: str = Form(...),
    department: str = Form(...),
    allowed_roles: str = Form(...), # comma separated
    current_user: models.User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    roles_list = [r.strip() for r in allowed_roles.split(',')]
    
    # Save to db
    doc_meta = models.DocumentMetadata(
        filename=file.filename,
        source_type=os.path.splitext(file.filename)[1].replace('.', '').upper(),
        classification=classification,
        department=department,
        allowed_roles=roles_list,
        uploader_id=current_user.id
    )
    db.add(doc_meta)
    db.commit()
    db.refresh(doc_meta)
    
    metadata = {
        "filename": doc_meta.filename,
        "classification": doc_meta.classification,
        "department": doc_meta.department,
        "allowed_roles": doc_meta.allowed_roles,
        "document_id": doc_meta.id
    }
    
    background_tasks.add_task(process_and_index_document, file_path, metadata, db)
    
    # Audit log
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="UPLOAD_DOCUMENT",
        target=file.filename,
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "File uploaded and indexing started", "document_id": doc_meta.id}

@router.get("/audit_logs")
def get_audit_logs(skip: int = 0, limit: int = 100, current_user: models.User = Depends(require_role(["ADMIN", "AUDITOR"])), db: Session = Depends(get_db)):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/security_logs")
def get_security_logs(skip: int = 0, limit: int = 100, current_user: models.User = Depends(require_role(["ADMIN", "SECURITY", "AUDITOR"])), db: Session = Depends(get_db)):
    logs = db.query(models.SecurityLog).order_by(models.SecurityLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs
