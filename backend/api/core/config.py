import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Database location: check for getitright.db in C# api directory or fallback to local backend dir
DEFAULT_DB_PATH = ROOT_DIR / "backend" / "csharp" / "GetItRight.Api" / "getitright.db"
if not DEFAULT_DB_PATH.exists():
    DEFAULT_DB_PATH = BASE_DIR / "getitright.db"

class Settings(BaseSettings):
    PROJECT_NAME: str = "GetItRight Unified Sovereign Voting & Polling API"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "getitright_super_secure_sovereign_secret_key_2026_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()
