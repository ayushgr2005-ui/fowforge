from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fowforge:fowforge@postgres:5432/fowforge"
    redis_url: str = "redis://redis:6379/0"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    top_k: int = Field(default=6, ge=1, le=20)
    min_retrieval_score: float = Field(default=0.25, ge=0.0, le=1.0)
    rate_limit_per_minute: int = Field(default=30, ge=1, le=10000)
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = Field(default=10, ge=1, le=100)
    auth_enabled: bool = False
    api_key: str = ""
    environment: str = "development"
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
