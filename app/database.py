from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine


# Формат строки подключения для SQL Server:
# mssql+pyodbc://<username>:<password>@<server>/<database>?driver=ODBC+Driver+17+for+SQL+Server
DATABASE_URL = "mssql+pyodbc://@localhost/kanban?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
#Генератор сессий БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()