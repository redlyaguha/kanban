from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from fastapi.responses import FileResponse
from .auth import get_current_user, oauth2_scheme, verify_password, create_access_token
from app.auth import verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from .crud import authenticate_user
from sqlalchemy import exists, func

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@app.post("/projects/", response_model=schemas.ProjectResponse)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_project(db=db, project=project, owner_id=current_user.id)

@app.post("/projects/{project_id}/add-member/")
def add_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.add_user_to_project(db=db, project_id=project_id, user_id=user_id)


@app.post("/columns/{column_id}/tasks/", response_model=schemas.TaskResponse)
def create_task(
        column_id: int,
        task: schemas.TaskCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    column = db.query(models.Column).filter(
        models.Column.id == column_id,
        models.Column.is_active == True
    ).first()
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена или неактивна")

    db_task = models.Task(**task.dict(), column_id=column_id, author_id=current_user.id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),  # OAuth2PasswordRequestForm
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)  # form_data.username → email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "kanban"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/ico/kanbanicon.ico")

@app.get("/users/", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return crud.get_users(db)


@app.post("/projects/{project_id}/columns/", response_model=schemas.ColumnResponse)
def create_column(
    project_id: int,
    column: schemas.ColumnCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Проверка активности проекта
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.is_active == True
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден или неактивен")
    db_column = models.Column(**column.dict(), project_id=project_id)
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    return crud.create_column(db=db, column=column, project_id=project_id)


@app.delete("/projects/{project_id}")
def deactivate_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = crud.delete_project(db, project_id)
    return result

@app.post("/projects/{project_id}/restore")
def restore_project_route(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = crud.restore_project(db, project_id)
    return result


@app.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(
        project_id: int,
        project_update: schemas.ProjectCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    if db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    updated_project = crud.update_project(db, project_id, project_update.name)
    return updated_project


@app.put("/columns/{column_id}", response_model=schemas.ColumnResponse)
def update_column(
        column_id: int,
        column_update: schemas.ColumnCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    db_column = crud.get_column(db, column_id)
    if not db_column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")
    if db_column.project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    updated_column = crud.update_column(db, column_id, column_update.name, column_update.order)
    return updated_column


@app.delete("/columns/{column_id}")
def deactivate_column(column_id: int, db: Session = Depends(get_db)):
    result = crud.delete_column(db, column_id)
    return result


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
        task_id: int,
        task_update: schemas.TaskCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    db_task = crud.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if db_task.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    updated_task = crud.update_task(db, task_id, task_update.title, task_update.description, task_update.priority)
    return updated_task


@app.delete("/tasks/{task_id}")
def deactivate_task(task_id: int, db: Session = Depends(get_db)):
    result = crud.delete_task(db, task_id)
    return result

    crud.delete_task(db, task_id)
    return {"message": "Задача удалена"}
@app.delete("/projects/{project_id}/remove-member/{user_id}")
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.remove_user_from_project(db, project_id, user_id)
@app.get("/columns/{column_id}/tasks/", response_model=list[schemas.TaskResponse])
def read_tasks_by_column(column_id: int, priority: int = None, db: Session = Depends(get_db)):
    return crud.get_tasks_by_column(db, column_id, priority)
@app.get("/projects/all", response_model=list[schemas.ProjectResponse])
def get_all_projects(
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    return crud.get_projects(db, is_active)
@app.get("/tasks/{task_id}/logs/", response_model=list[schemas.TaskLogResponse])
def read_task_logs(task_id: int, db: Session = Depends(get_db)):
    logs = crud.get_task_logs(db, task_id)
    if not logs:
        raise HTTPException(status_code=404, detail="Логи не найдены")
    return logs

@app.post("/columns/{column_id}/restore")
def restore_column_route(column_id: int, db: Session = Depends(get_db)):
    result = crud.restore_column(db, column_id)
    return result

@app.post("/tasks/{task_id}/restore")
def restore_task_route(task_id: int, db: Session = Depends(get_db)):
    result = crud.restore_task(db, task_id)
    return result


@app.get("/projects/me/", response_model=list[schemas.ProjectDetails])
def read_user_projects(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    # Проекты, где пользователь - владелец
    owned = db.query(models.Project).filter(
        models.Project.owner_id == current_user.id,
        models.Project.is_active == True
    ).all()

    # Проекты, где пользователь - участник
    member = db.query(models.Project).join(models.ProjectMember).filter(
        models.ProjectMember.user_id == current_user.id,
        models.Project.is_active == True
    ).all()

    # Объедините списки и уберите дубликаты
    projects = list(set(owned + member))

    # Подсчет задач и формирование ответа
    result = []
    for project in projects:
        task_count = db.query(func.count(models.Task.id)).join(models.Column).filter(
            models.Column.project_id == project.id,
            models.Task.is_active == True  # Учет активности задач
        ).scalar()

        result.append({
            "id": project.id,
            "name": project.name,
            "owner_id": project.owner_id,
            "task_count": task_count,
            "members": [schemas.ProjectMemberResponse(**u.__dict__) for u in project.members]
        })

    return result