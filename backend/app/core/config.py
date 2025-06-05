from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Carbon Emissions Intelligence Platform"
    database_url: str = "postgresql://postgres:Vijay1825%40@localhost:5432/carbon_db"
    debug: bool = False
    
    # API Keys for data ingestion
    epa_api_key: Optional[str] = None
    defra_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
