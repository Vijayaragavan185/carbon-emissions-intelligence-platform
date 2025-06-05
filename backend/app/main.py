from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import emissions
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(emissions.router, prefix="/api", tags=["emissions"])

@app.get("/")
def root():
    return {"message": "Carbon Emissions Intelligence Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
