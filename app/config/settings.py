from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    APP_NAME: str = "Instagram AI Automation SaaS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security
    SECRET_KEY: str = "replace_with_a_super_secret_jwt_key_at_least_32_chars_long"
    ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/instagram_saas"
    DB_APP_USER: str = "saas_app_user"
    DB_APP_PASSWORD: str = "saas_app_password"
    DB_WORKER_USER: str = "saas_worker_user"
    DB_WORKER_PASSWORD: str = "saas_worker_password"
    DB_INGEST_USER: str = "saas_ingest_user"
    DB_INGEST_PASSWORD: str = "saas_ingest_password"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Meta Graph API
    META_APP_ID: str = "your_meta_app_id"
    META_APP_SECRET: str = "your_meta_app_secret"
    META_WEBHOOK_VERIFY_TOKEN: str = "your_custom_webhook_verification_token"
    META_GRAPH_API_VERSION: str = "v21.0"
    META_GRAPH_API_BASE_URL: str = "https://graph.facebook.com"

    @property
    def meta_api_endpoint(self) -> str:
        return f"{self.META_GRAPH_API_BASE_URL}/{self.META_GRAPH_API_VERSION}"

    # AI Integration
    OPENROUTER_API_KEY: Optional[str] = None
    DEFAULT_AI_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Storage
    STORAGE_PROVIDER: str = "minio"
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "saas-knowledge-base"
    S3_REGION: str = "us-east-1"

    # Payment Gateways
    PAYME_MERCHANT_ID: Optional[str] = None
    PAYME_SECRET_KEY: Optional[str] = None
    CLICK_SERVICE_ID: Optional[str] = None
    CLICK_MERCHANT_ID: Optional[str] = None
    CLICK_SECRET_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None


settings = Settings()
