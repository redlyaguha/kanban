from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, Boolean, Text, DateTime, func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    projects: Mapped[list["Project"]] = relationship(secondary="project_members", back_populates="members")

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    members: Mapped[list["User"]] = relationship(secondary="project_members", back_populates="projects")
    columns: Mapped[list["Column"]] = relationship(back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

class Column(Base):
    __tablename__ = "columns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer, default=0)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Добавлено
    project: Mapped["Project"] = relationship(back_populates="columns")
    tasks: Mapped[list["Task"]] = relationship(back_populates="column")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    priority: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Добавлено
    column: Mapped["Column"] = relationship(back_populates="tasks")
    logs: Mapped[list["TaskLog"]] = relationship(back_populates="task")

class TaskLog(Base):
    __tablename__ = "task_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    message: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    task: Mapped["Task"] = relationship(back_populates="logs")