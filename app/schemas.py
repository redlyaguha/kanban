from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(ProjectCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 2

class TaskResponse(TaskCreate):
    id: int
    author_id: int
    column_id: int
    created_at: datetime
    is_active: bool  # Добавлено
    class Config:
        from_attributes = True

class TaskLogResponse(BaseModel):
    message: str
    created_at: datetime
    user_id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ColumnCreate(BaseModel):
    name: str
    order: Optional[int] = 0

class ColumnResponse(ColumnCreate):
    id: int
    project_id: int
    is_active: bool  # Добавлено
    class Config:
        from_attributes = True
class ProjectMemberResponse(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True

class ProjectDetails(ProjectResponse):
    members: List[ProjectMemberResponse] = []
    task_count: int = 0
    class Config:
        from_attributes = True

