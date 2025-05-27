from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from .auth import verify_password

# Users
def get_users(db: Session):
    """Возвращает список всех пользователей."""
    return db.query(models.User).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)  # Используем хеширование
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Projects
def create_project(db: Session, project: schemas.ProjectCreate, owner_id: int):
    db_project = models.Project(**project.model_dump(), owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def add_user_to_project(db: Session, project_id: int, user_id: int):
    db_member = models.ProjectMember(project_id=project_id, user_id=user_id)
    db.add(db_member)
    db.commit()
    return db_member

# Tasks
def create_task(db: Session, task: schemas.TaskCreate, column_id: int, author_id: int):
    # Проверка активности проекта через колонку
    column = db.query(models.Column).filter(
        models.Column.id == column_id,
        models.Column.project.has(is_active=True)
    ).first()
    if not column:
        raise HTTPException(status_code=404, detail="Колонка или проект неактивны")
    # Создание задачи...
    db_task = models.Task(**task.model_dump(), column_id=column_id, author_id=author_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    """Проверяет email и пароль пользователя."""
    user = get_user_by_email(db, email)  # Предполагается, что эта функция уже есть в crud.py
    if not user:
        return None  # Пользователь не найден
    if not verify_password(password, user.hashed_password):
        return None  # Пароль неверный
    return user  # Аутентификация успешна

def create_column(db: Session, column: schemas.ColumnCreate, project_id: int):
    db_column = models.Column(**column.dict(), project_id=project_id)
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    return db_column  # Возвращает ORM-объект, без Session


def get_project(db: Session, project_id: int):
    return db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.is_active == True
    ).first()

def delete_project(db: Session, project_id: int):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    project.is_active = False  # Мягкое удаление
    db.commit()
    return {"message": "Проект деактивирован"}

def restore_project(db: Session, project_id: int):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    project.is_active = True  # Восстановление
    db.commit()
    return {"message": "Проект восстановлен"}