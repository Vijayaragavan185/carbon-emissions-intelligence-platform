import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base

# Use the same DB URL as your application
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Vijay1825%40@localhost:5432/carbon_db"

@pytest.fixture
def db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Optional: clean up after tests
