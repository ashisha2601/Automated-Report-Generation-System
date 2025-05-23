from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create the database directory if it doesn't exist
os.makedirs("app/data", exist_ok=True)

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./app/data/app.db"

# Create SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    from app.models.user import User
    from app.models.history import History
    Base.metadata.create_all(bind=engine)
