from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Путь к БД: backend/app/data/invest_edu.db
BASE_DIR = Path(__file__).parent.parent  # backend/app
DATA_DIR = BASE_DIR / "data"

# Создаём директорию если не существует
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "invest_edu.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
