from pydantic import BaseModel
from datetime import datetime

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
    description: str | None = None
    priority: int = 2

class TaskResponse(TaskCreate):
    id: int
    author_id: int
    column_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TaskLogResponse(BaseModel):
    message: str
    created_at: datetime
    user_id: int
    class Config:
        from_attributes = True