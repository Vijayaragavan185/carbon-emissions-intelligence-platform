from pydantic_settings import BaseSettings
from typing import Dict, Any
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Use your existing database URL
    DATABASE_URL: str = "postgresql://postgres:Vijay1825%40@localhost:5432/carbon_db"
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Carbon Emissions Intelligence Platform"
    
    # ESG Integration settings
    ESG_INTEGRATIONS: Dict[str, Any] = {
        "cdp": {
            "base_url": "https://api.cdp.net",
            "api_key": "test_key",
            "organization_id": "test_org"
        },
        "edci": {
            "base_url": "https://api.edci.net", 
            "api_key": "test_key",
            "firm_id": "test_firm"
        },
        "lseg": {
            "base_url": "https://api.lseg.com",
            "client_id": "test_client",
            "client_secret": "test_secret"
        },
        "webhooks": {
            "test_webhook": {
                "url": "http://localhost:8080/webhook",
                "events": ["report.submitted", "report.approved"],
                "secret": "test_secret"
            }
        }
    }
    
    class Config:
        env_file = ".env"

settings = Settings()
