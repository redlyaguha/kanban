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
from sqlalchemy import exists

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
    # Проверка существования колонки
    column = db.query(models.Column).filter(models.Column.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Колонка не найдена")

    # Создание задачи
    db_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        column_id=column_id,
        author_id=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task  # Возвращаем ORM-объект, который конвертируется в TaskResponse


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
    # Проверка, существует ли проект
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # Проверка прав
    if db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    return crud.create_column(db=db, column=column, project_id=project_id)

@app.put("/tasks/{task_id}/move/", response_model=schemas.TaskResponse)
def move_task(
    task_id: int,
    task_move: schemas.TaskMove,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.move_task(
        db=db,
        task_id=task_id,
        new_column_id=task_move.new_column_id,
        user_id=current_user.id
    )

@app.delete("/projects/{project_id}", response_model=schemas.ProjectDeleteResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.delete_project(db=db, project_id=project_id, user_id=current_user.id)