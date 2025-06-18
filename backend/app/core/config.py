from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings for Carbon Emissions Intelligence Platform"""
    
    # ==== BASIC APPLICATION SETTINGS ====
    PROJECT_NAME: str = "Carbon Emissions Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ==== API SETTINGS ====
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # ==== DATABASE SETTINGS ====
    DATABASE_URL: str = "postgresql://postgres:Vijay1825%40@localhost:5432/carbon_db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False  # Set to True for SQL query logging
    
    # ==== SECURITY SETTINGS ====
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # ==== CORS SETTINGS ====
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8080",  # Alternative frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # ==== FILE STORAGE SETTINGS ====
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".json", ".pdf"]
    
    # ==== LOGGING SETTINGS ====
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "midnight"
    LOG_RETENTION: int = 30  # days
    
    # ==== REDIS SETTINGS (for caching and background tasks) ====
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1 hour
    
    # ==== EMAIL SETTINGS ====
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # ==== ESG FRAMEWORK SETTINGS ====
    DEFAULT_EMISSION_FACTOR_SOURCE: str = "EPA"
    SUPPORTED_FRAMEWORKS: List[str] = ["cdp", "tcfd", "eu_taxonomy", "gri", "sasb"]
    DEFAULT_REPORTING_YEAR: int = 2024
    
    # ==== ML MODEL SETTINGS ====
    MODEL_CACHE_DIR: str = "models/cache"
    MODEL_RETRAIN_INTERVAL_DAYS: int = 30
    PREDICTION_BATCH_SIZE: int = 1000
    MODEL_VALIDATION_THRESHOLD: float = 0.8
    
    # ==== API RATE LIMITING ====
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # ==== EXTERNAL API KEYS ====
    EPA_API_KEY: Optional[str] = None
    DEFRA_API_KEY: Optional[str] = None
    IPCC_API_KEY: Optional[str] = None
    
    # ==== ESG INTEGRATION SETTINGS ====
    ESG_INTEGRATIONS: Dict[str, Any] = {
        "cdp": {
            "enabled": True,
            "base_url": "https://api.cdp.net",
            "api_key": "test_key",
            "organization_id": "test_org",
            "timeout": 30,
            "retry_attempts": 3,
            "questionnaire_types": ["climate_change", "water_security", "forests"],
            "default_questionnaire": "climate_change"
        },
        "tcfd": {
            "enabled": True,
            "base_url": "https://api.tcfd.org",
            "api_key": "test_key",
            "timeout": 30,
            "retry_attempts": 3,
            "pillars": ["governance", "strategy", "risk_management", "metrics_targets"]
        },
        "edci": {
            "enabled": True,
            "base_url": "https://api.edci.net",
            "api_key": "test_key",
            "firm_id": "test_firm",
            "timeout": 30,
            "retry_attempts": 3,
            "reporting_year": 2024
        },
        "lseg": {
            "enabled": True,
            "base_url": "https://api.lseg.com",
            "client_id": "test_client",
            "client_secret": "test_secret",
            "timeout": 30,
            "retry_attempts": 3,
            "data_types": ["scores", "measures", "basic"]
        },
        "eu_taxonomy": {
            "enabled": True,
            "version": "2024",
            "environmental_objectives": [
                "climate_change_mitigation",
                "climate_change_adaptation",
                "sustainable_water_marine",
                "circular_economy",
                "pollution_prevention",
                "biodiversity_ecosystems"
            ],
            "kpi_types": ["turnover", "capex", "opex"]
        }
    }
    
    # ==== WEBHOOK SETTINGS ====
    WEBHOOK_SETTINGS: Dict[str, Any] = {
        "enabled": True,
        "max_retries": 3,
        "retry_delay": 60,  # seconds
        "timeout": 30,
        "default_events": [
            "report.created",
            "report.submitted", 
            "report.approved",
            "report.rejected",
            "report.published"
        ],
        "webhooks": {
            "test_webhook": {
                "url": "http://localhost:8080/webhook",
                "events": ["report.submitted", "report.approved"],
                "secret": "test_secret",
                "active": True
            }
        }
    }
    
    # ==== APPROVAL WORKFLOW SETTINGS ====
    APPROVAL_WORKFLOWS: Dict[str, Any] = {
        "cdp": {
            "levels": [
                {
                    "level": 1,
                    "title": "Data Manager Review",
                    "required_role": "data_manager",
                    "auto_advance": False
                },
                {
                    "level": 2,
                    "title": "Sustainability Manager Approval",
                    "required_role": "sustainability_manager",
                    "auto_advance": False
                },
                {
                    "level": 3,
                    "title": "Executive Approval",
                    "required_role": "executive",
                    "auto_advance": False
                }
            ],
            "parallel_approval": False,
            "auto_publish": False
        },
        "tcfd": {
            "levels": [
                {
                    "level": 1,
                    "title": "Risk Manager Review",
                    "required_role": "risk_manager",
                    "auto_advance": False
                },
                {
                    "level": 2,
                    "title": "CFO Approval",
                    "required_role": "cfo",
                    "auto_advance": False
                },
                {
                    "level": 3,
                    "title": "CEO Final Approval",
                    "required_role": "ceo",
                    "auto_advance": False
                }
            ],
            "parallel_approval": False,
            "auto_publish": False
        },
        "eu_taxonomy": {
            "levels": [
                {
                    "level": 1,
                    "title": "Legal Review",
                    "required_role": "legal",
                    "auto_advance": False
                },
                {
                    "level": 2,
                    "title": "Finance Review",
                    "required_role": "finance",
                    "auto_advance": True
                },
                {
                    "level": 3,
                    "title": "Board Approval",
                    "required_role": "board_member",
                    "auto_advance": False
                }
            ],
            "parallel_approval": True,  # Level 1 and 2 can run in parallel
            "auto_publish": False
        }
    }
    
    # ==== PDF GENERATION SETTINGS ====
    PDF_SETTINGS: Dict[str, Any] = {
        "default_template": {
            "company_name": "Carbon Emissions Intelligence Platform",
            "logo_path": None,
            "primary_color": "#2E7D32",  # Green
            "secondary_color": "#1565C0",  # Blue
            "accent_color": "#FF6F00",  # Orange
            "font_family": "Helvetica",
            "header_font_size": 16,
            "body_font_size": 10,
            "footer_text": "Generated by Carbon Emissions Intelligence Platform",
            "watermark": None
        },
        "output_directory": "reports/pdf",
        "temp_directory": "temp/pdf",
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "quality": "high",
        "compression": True
    }
    
    # ==== VALIDATION SETTINGS ====
    VALIDATION_SETTINGS: Dict[str, Any] = {
        "strict_mode": False,
        "auto_fix_errors": True,
        "max_error_threshold": 10,
        "data_quality_thresholds": {
            "excellent": 95,
            "good": 85,
            "acceptable": 70,
            "poor": 50
        },
        "compliance_score_weights": {
            "completeness": 0.4,
            "accuracy": 0.3,
            "consistency": 0.2,
            "timeliness": 0.1
        }
    }
    
    # ==== MONITORING AND HEALTH CHECK SETTINGS ====
    HEALTH_CHECK_SETTINGS: Dict[str, Any] = {
        "enabled": True,
        "check_interval": 300,  # 5 minutes
        "endpoints": [
            "/health",
            "/api/health",
            "/api/esg/integration-health"
        ],
        "external_services": [
            "database",
            "redis",
            "cdp_api",
            "lseg_api"
        ],
        "alert_thresholds": {
            "response_time_ms": 5000,
            "error_rate_percent": 5,
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85
        }
    }
    
    # ==== BACKUP AND ARCHIVE SETTINGS ====
    BACKUP_SETTINGS: Dict[str, Any] = {
        "enabled": True,
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "retention_days": 90,
        "backup_location": "backups/",
        "compress": True,
        "include_files": True,
        "encrypt": False
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow extra fields for flexibility
        extra = "allow"

# Create settings instance
settings = Settings()

# ==== HELPER FUNCTIONS ====
def get_database_url() -> str:
    """Get database URL with proper encoding"""
    return settings.DATABASE_URL

def is_production() -> bool:
    """Check if running in production environment"""
    return settings.ENVIRONMENT.lower() == "production"

def is_development() -> bool:
    """Check if running in development environment"""
    return settings.ENVIRONMENT.lower() == "development"

def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    if is_production():
        # In production, restrict CORS origins
        return [origin for origin in settings.BACKEND_CORS_ORIGINS if not origin.startswith("http://localhost")]
    return settings.BACKEND_CORS_ORIGINS

def get_log_config() -> Dict[str, Any]:
    """Get logging configuration"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.LOG_FILE,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
            },
        },
    }

# ==== VALIDATION FUNCTIONS ====
def validate_settings():
    """Validate settings on startup"""
    errors = []
    
    # Check required database URL
    if not settings.DATABASE_URL.startswith("postgresql://"):
        errors.append("DATABASE_URL must be a PostgreSQL connection string")
    
    # Check secret key in production
    if is_production() and settings.SECRET_KEY == "your-secret-key-change-this-in-production":
        errors.append("SECRET_KEY must be changed in production")
    
    # Check upload directory exists
    upload_path = Path(settings.UPLOAD_DIR)
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)
    
    # Check logs directory exists
    log_path = Path(settings.LOG_FILE).parent
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=True)
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True

# Validate settings on import
try:
    validate_settings()
except ValueError as e:
    print(f"⚠️ Configuration Warning: {e}")

# Export commonly used settings
__all__ = [
    "settings",
    "get_database_url",
    "is_production", 
    "is_development",
    "get_cors_origins",
    "get_log_config",
    "validate_settings"
]
