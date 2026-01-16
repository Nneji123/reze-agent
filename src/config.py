"""Configuration settings for Reze AI Agent."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main settings container with flat structure for .env reading."""

    # Application Settings
    debug: bool = Field(default=True, env="DEBUG", description="Enable debug mode")
    host: str = Field(default="0.0.0.0", env="HOST", description="Server host address")
    port: int = Field(default=8000, env="PORT", description="Server port number")
    log_level: str = Field(default="INFO", env="LOG_LEVEL", description="Logging level")
    sentry_dsn: str = Field(
        default="",
        env="SENTRY_DSN",
        description="Sentry DSN for error tracking",
    )

    # GLM 4.7 AI Provider Settings
    glm_api_key: str = Field(
        default="test_glm_key",
        env="GLM_API_KEY",
        description="GLM 4.7 API key from z.ai",
    )
    glm_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        env="GLM_BASE_URL",
        description="GLM 4.7 base URL (OpenAI-compatible)",
    )
    glm_model: str = Field(
        default="glm-4.7",
        env="GLM_MODEL",
        description="GLM model name",
    )

    # Resend.com API Settings
    resend_api_key: str = Field(
        default="re_test_key",
        env="RESEND_API_KEY",
        description="Resend API key",
    )
    resend_from_email: str = Field(
        default="test@example.com",
        env="RESEND_FROM_EMAIL",
        description="Default sender email address",
    )
    resend_base_url: str = Field(
        default="https://api.resend.com",
        env="RESEND_BASE_URL",
        description="Resend API base URL",
    )

    # Memvid RAG Settings
    memvid_file_path: str = Field(
        default="./memory.mv2",
        env="MEMVID_FILE_PATH",
        description="Path to Memvid knowledge base file",
    )
    memvid_index_kind: str = Field(
        default="basic",
        env="MEMVID_INDEX_KIND",
        description="Memvid index kind (basic or advanced)",
    )

    # Database Settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./database",
        env="DATABASE_URL",
        description="SQLAlchemy database URL",
    )
    database_echo: bool = Field(
        default=False,
        env="DATABASE_ECHO",
        description="Enable SQLAlchemy query logging",
    )

    @field_validator("glm_base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("GLM base URL must start with http:// or https://")
        return v

    @field_validator("resend_from_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v

    @field_validator("memvid_index_kind")
    @classmethod
    def validate_index_kind(cls, v: str) -> str:
        """Validate index kind."""
        allowed_kinds = ["basic", "advanced"]
        if v not in allowed_kinds:
            raise ValueError(f"Index kind must be one of {allowed_kinds}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
