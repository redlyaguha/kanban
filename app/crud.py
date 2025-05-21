from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from .auth import verify_password
from fastapi import HTTPException

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
    return db_column


def move_task(db: Session, task_id: int, new_column_id: int, user_id: int):
    # Находим задачу
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Находим новую колонку
    new_column = db.query(models.Column).filter(models.Column.id == new_column_id).first()
    if not new_column:
        raise HTTPException(status_code=404, detail="Новая колонка не найдена")

    # Проверка прав: автор задачи или участник проекта
    project = new_column.project  # Получаем проект, к которому относится новая колонка
    if db_task.author_id != user_id and user_id not in [m.user_id for m in project.members]:
        raise HTTPException(status_code=403, detail="Нет прав на перемещение")



    # Обновляем колонку задачи
    db_task.column_id = new_column_id
    db.commit()
    db.refresh(db_task)

    # Логирование действия
    if not task_id:
        raise ValueError("Task ID cannot be None")

    log_message = f"Задача перемещена в колонку '{new_column.name}'"
    db_log = models.TaskLog(
        task_id=task_id,
        user_id=user_id,
        message=log_message
    )
    db.add(db_log)
    db.commit()

    return db_task


def delete_project(db: Session, project_id: int, user_id: int):
    db_project = db.query(models.Project).get(project_id)

    # Проверка прав
    if db_project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    # Ручное каскадное удаление
    for column in db_project.columns:
        for task in column.tasks:
            # Удаляем все логи задачи
            db.query(models.TaskLog).filter(models.TaskLog.task_id == task.id).delete()
            # Удаляем саму задачу
            db.delete(task)
        db.delete(column)

    db.delete(db_project)
    db.commit()

    return {"status": "success", "message": "Проект удален"}

