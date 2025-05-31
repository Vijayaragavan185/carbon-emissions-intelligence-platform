import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models.emissions import Base

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Vijay1825%40@localhost:5432/carbon_db"

@pytest.fixture(scope="function")
def db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up after each test
        Base.metadata.drop_all(bind=engine)
