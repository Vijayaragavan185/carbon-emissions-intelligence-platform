from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Carbon Emissions Intelligence Platform"
    database_url: str = "postgresql://user:password@postgres:5432/carbon_db"
    debug: bool = False

settings = Settings()
