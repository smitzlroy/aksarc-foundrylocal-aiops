"""Application configuration using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # Foundry Local Configuration
    foundry_endpoint: str = Field(
        default="http://127.0.0.1:58366",
        description="Foundry Local endpoint URL",
    )
    foundry_model: str = Field(
        default="qwen2.5-0.5b",
        description="Foundry model to use",
    )
    foundry_timeout: float = Field(
        default=30.0,
        description="Foundry request timeout in seconds",
    )

    # Kubernetes Configuration
    kubeconfig: str | None = Field(
        default=None,
        description="Path to kubeconfig file (None = use default)",
    )
    k8s_namespace: str | None = Field(
        default=None,
        description="Default namespace to watch (None = all namespaces)",
    )

    # Context Buffer Configuration
    context_buffer_hours: int = Field(
        default=2,
        description="Number of hours of data to keep in buffer",
    )
    max_buffer_size_mb: int = Field(
        default=500,
        description="Maximum buffer size in megabytes",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or console)",
    )

    # Application Metadata
    app_name: str = Field(
        default="AKS Arc AI Ops Assistant",
        description="Application name",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
    )


# Global settings instance
settings = Settings()
