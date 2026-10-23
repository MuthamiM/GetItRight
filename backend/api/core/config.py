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
    VERSION: str = "2.1.34"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "production"

    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"

    # Required at process startup; never fall back to a checked-in signing key.
    SECRET_KEY: str = Field(min_length=32)
    # Dedicated persistent key for encrypted browser snapshots and consented profiles.
    BROWSER_STORAGE_ENCRYPTION_KEY: str = Field(default="", repr=False)
    JWT_ISSUER: str = "getitright-api"
    JWT_AUDIENCE: str = "getitright-clients"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    PAYMENT_PROVIDER: str = "ipay"
    IPAY_VENDOR_ID: str = ""
    IPAY_HASH_KEY: str = ""
    IPAY_LIVE: str = "0"
    FLW_SECRET_KEY: str = ""
    FLW_SECRET_HASH: str = ""
    APP_PUBLIC_URL: str = "https://icapsq.mftechnologies.org"

    # Comma-separated explicit origin allowlist.
    CORS_ORIGINS: str = "https://icapsq.mftechnologies.org"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "info@mftechnologies.org"
    RESEND_TEST_RECIPIENT: str = ""
    PASSWORD_RESET_URL: str = "https://icapsq.mftechnologies.org/auth/forgot-password.html"

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
        if self.PAYMENT_PROVIDER.strip().lower() not in {"ipay", "flutterwave"}:
            raise ValueError("PAYMENT_PROVIDER must be ipay or flutterwave")
        if self.IPAY_LIVE not in {"0", "1"}:
            raise ValueError("IPAY_LIVE must be 0 or 1")
        if not self.SECRET_KEY or self.SECRET_KEY.startswith("getitright_"):
            raise ValueError("SECRET_KEY must be a unique deployment secret of at least 32 characters")
        if self.ENVIRONMENT.lower() == "production":
            if not self.BROWSER_STORAGE_ENCRYPTION_KEY:
                raise ValueError("BROWSER_STORAGE_ENCRYPTION_KEY must be configured in production")
            try:
                from cryptography.fernet import Fernet
                Fernet(self.BROWSER_STORAGE_ENCRYPTION_KEY.encode("ascii"))
            except (UnicodeEncodeError, ValueError):
                raise ValueError("BROWSER_STORAGE_ENCRYPTION_KEY must be a valid Fernet key") from None
        if not self.cors_origins or "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS must contain explicit trusted origins")
        if self.ENVIRONMENT.lower() == "production" and any(
            origin.startswith("http://") for origin in self.cors_origins
        ):
            raise ValueError("Production CORS origins must use HTTPS")
        if self.ENVIRONMENT.lower() == "production":
            if not self.APP_PUBLIC_URL.startswith("https://"):
                raise ValueError("APP_PUBLIC_URL must use HTTPS in production")
            if not self.PASSWORD_RESET_URL.startswith("https://"):
                raise ValueError("PASSWORD_RESET_URL must use HTTPS in production")
            if self.RESEND_TEST_RECIPIENT:
                raise ValueError("RESEND_TEST_RECIPIENT must be empty in production")
            if self.RESEND_API_KEY and self.RESEND_FROM_EMAIL.lower().endswith("@resend.dev"):
                raise ValueError("Configure a verified sender domain for production email")
        return self

settings = Settings()
