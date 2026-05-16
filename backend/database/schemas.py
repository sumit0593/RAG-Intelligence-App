from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RoleBase(BaseModel):
    name: str

class Role(RoleBase):
    id: int
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    department: str
    role_id: int

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: Role
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class DocumentMetadataBase(BaseModel):
    filename: str
    source_type: str
    classification: str
    department: str
    allowed_roles: List[str]

class DocumentMetadata(DocumentMetadataBase):
    id: int
    uploaded_at: datetime
    uploader_id: int
    class Config:
        from_attributes = True
