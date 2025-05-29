from fastapi import FastAPI
from app.api.endpoints import emissions
from app.db.session import SessionLocal, Base, engine

app = FastAPI()
app.include_router(emissions.router, prefix="/api/v1")

Base.metadata.create_all(bind=engine)
