from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from .auth import verify_password
from sqlalchemy import func
from .models import Task, Column


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
def update_project(db: Session, project_id: int, new_name: str):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    db_project.name = new_name
    db.commit()
    db.refresh(db_project)
    return db_project

def get_column(db: Session, column_id: int):
    return db.query(models.Column).filter(models.Column.id == column_id, models.Column.is_active == True).first()

def delete_column(db: Session, column_id: int):
    column = get_column(db, column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")
    column.is_active = False  # Мягкое удаление
    db.commit()
    return {"message": "Колонка деактивирована"}

def restore_column(db: Session, column_id: int):
    column = db.query(models.Column).filter(models.Column.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")
    column.is_active = True  # Восстановление
    db.commit()
    return {"message": "Колонка восстановлена"}

def update_column(db: Session, column_id: int, new_name: str, new_order: int):
    db_column = get_column(db, column_id)
    db_column.name = new_name
    db_column.order = new_order
    db.commit()
    db.refresh(db_column)
    return db_column



def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id, models.Task.is_active == True).first()

def delete_task(db: Session, task_id: int):
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    task.is_active = False  # Мягкое удаление
    db.commit()
    return {"message": "Задача деактивирована"}

def restore_task(db: Session, task_id: int):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    task.is_active = True  # Восстановление
    db.commit()
    return {"message": "Задача восстановлена"}

def update_task(db: Session, task_id: int, new_title: str, new_description: str, new_priority: int):
    db_task = get_task(db, task_id)
    db_task.title = new_title
    db_task.description = new_description
    db_task.priority = new_priority
    db.commit()
    db.refresh(db_task)
    return db_task



def remove_user_from_project(db: Session, project_id: int, user_id: int):
    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Пользователь не состоит в проекте")

    db.delete(member)
    db.commit()
    return {"message": "Пользователь удален из проекта"}
def get_tasks_by_column(db: Session, column_id: int, priority: int = None):
    query = db.query(models.Task).filter(models.Task.column_id == column_id, models.Task.is_active == True)
    if priority is not None:
        query = query.filter(models.Task.priority == priority)
    return query.all()

def get_projects(db: Session, is_active: bool = True):
    return db.query(models.Project).filter(models.Project.is_active == is_active).all()

def get_task_logs(db: Session, task_id: int):
    return db.query(models.TaskLog).filter(models.TaskLog.task_id == task_id).all()

def get_task_count_by_project(db: Session, project_id: int):
    return db.query(func.count(Task.id)).join(Column).filter(Column.project_id == project_id).scalar()


