from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Carbon Emissions Intelligence Platform"
    database_url: str = "postgresql://user:password@postgres:5432/carbon_db"
    debug: bool = False

settings = Settings()
# Add these to your existing config.py
EPA_API_KEY: str = None
DEFRA_API_KEY: str = None

# If using environment variables
import os

EPA_API_KEY = os.getenv("EPA_API_KEY")
DEFRA_API_KEY = os.getenv("DEFRA_API_KEY")
