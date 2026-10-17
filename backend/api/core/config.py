from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

DEFAULT_DB_PATH = ROOT_DIR / "backend" / "csharp" / "GetItRight.Api" / "getitright.db"
if not DEFAULT_DB_PATH.exists():
    DEFAULT_DB_PATH = BASE_DIR / "getitright.db"

class Settings(BaseSettings):
    PROJECT_NAME: str = "IcapsQ API"
    VERSION: str = "2.1.2"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "production"

    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"

    # A deployment secret must be supplied through the environment. A checked-in
    # default is provided for local dev/testing.
    SECRET_KEY: str = Field(default="[REDACTED]", min_length=32)
    JWT_ISSUER: str = "getitright-api"
    JWT_AUDIENCE: str = "getitright-clients"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Comma-separated explicit origin allowlist.
    CORS_ORIGINS: str = "http://localhost:8888,http://localhost:8090,http://127.0.0.1:8888,http://127.0.0.1:8090"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    RESEND_TEST_RECIPIENT: str = ""
    PASSWORD_RESET_URL: str = "http://127.0.0.1:8090/auth/forgot-password.html"

    model_config = {
        "case_sensitive": True,
        "env_file": [str(ROOT_DIR / ".env"), str(BASE_DIR / ".env"), ".env"],
        "extra": "ignore"
    }

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_security_configuration(self):
        if not self.SECRET_KEY or self.SECRET_KEY.startswith("getitright_"):
            raise ValueError("SECRET_KEY must be a unique deployment secret of at least 32 characters")
        if not self.cors_origins or "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS must contain explicit trusted origins")
        if self.ENVIRONMENT.lower() == "production" and any(
            origin.startswith("http://") and "localhost" not in origin and "127.0.0.1" not in origin
            for origin in self.cors_origins
        ):
            raise ValueError("Production CORS origins must use HTTPS")
        return self

settings = Settings()
