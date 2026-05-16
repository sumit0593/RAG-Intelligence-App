from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.config import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., ADMIN, HR, FINANCE, ENGINEERING

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"))
    department = Column(String)

    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    security_logs = relationship("SecurityLog", back_populates="user")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String) # e.g., "QUERY", "UPLOAD_DOCUMENT"
    target = Column(String) # e.g., query string, or filename
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # e.g., "SUCCESS", "FAILED"

    user = relationship("User", back_populates="audit_logs")

class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String) # e.g., "UNAUTHORIZED_ACCESS_ATTEMPT"
    reason = Column(String) # e.g., "Attempted to access sensitive salary data"
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="security_logs")

class DocumentMetadata(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    source_type = Column(String) # PDF, CSV, JSON
    classification = Column(String) # PUBLIC, INTERNAL, CONFIDENTIAL, SENSITIVE
    department = Column(String) # HR, FINANCE, etc.
    allowed_roles = Column(JSON) # e.g., ["HR", "ADMIN"]
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploader_id = Column(Integer, ForeignKey("users.id"))

# Additional specific datasets for structured queries
class EmployeeRecord(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department = Column(String)
    role = Column(String)
    salary = Column(Integer) # Highly sensitive
    performance_rating = Column(String)

class FinancialReport(Base):
    __tablename__ = "financial_reports"
    id = Column(Integer, primary_key=True, index=True)
    quarter = Column(String)
    year = Column(Integer)
    revenue = Column(Integer)
    expenses = Column(Integer)
    status = Column(String) # e.g., "DRAFT", "FINAL"
