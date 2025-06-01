from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    app_name: str = "Carbon Emissions Intelligence Platform"
    database_url: str = "postgresql://user:password@postgres:5432/carbon_db"
    debug: bool = False
    
    # API Keys for data ingestion
    epa_api_key: Optional[str] = None
    defra_api_key: Optional[str] = None
    
    class Config:
        # This tells Pydantic to load from environment variables
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Convert environment variable names (EPA_API_KEY becomes epa_api_key)
        case_sensitive = False

settings = Settings()
