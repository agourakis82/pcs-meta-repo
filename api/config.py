"""Configuration settings for the PCS-HELIO MCP API."""

from pathlib import Path
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra environment variables
    )

    # API Configuration
    API_NAME: str = Field(default="PCS‑HELIO MCP API", description="API service name")
    ENV: str = Field(
        default="development", description="Environment (development, production)"
    )
    API_KEY_REQUIRED: bool = Field(
        default=False, description="Whether API key is required"
    )
    API_KEYS: str = Field(
        default="", description="API keys for authentication (comma-separated in env)"
    )

    @field_validator("API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v: Any) -> str:
        """Parse API_KEYS from string or list."""
        if isinstance(v, list):
            return ",".join(v)
        return str(v) if v else ""

    # Rate limiting settings
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST_CAPACITY: int = Field(default=10)
    RATE_LIMIT_REFILL_RATE: float = Field(default=1.0)

    # Cache settings
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching")
    CACHE_MEMORY_SIZE: int = Field(default=1000, description="Memory cache max size")
    CACHE_DEFAULT_TTL: int = Field(default=3600, description="Default TTL in seconds")
    REDIS_URL: Optional[str] = Field(default=None, description="Redis connection URL")
    CACHE_PREFIX: str = Field(default="pcs_cache:", description="Cache key prefix")

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-large", description="OpenAI embedding model"
    )

    # Chroma Configuration
    CHROMA_PATH: str = Field(
        default="./ragpp/index/lit2025", description="Path to Chroma database"
    )

    # Data Paths
    DATA_DIR: str = Field(default="./data", description="Base data directory")
    KEC_PARQUET_GLOB: str = Field(
        default="data/processed/kec/**/kec*.parquet",
        description="Glob pattern for KEC parquet files",
    )

    # Directory Paths
    NOTEBOOK_DIR: str = Field(
        default="./notebooks", description="Jupyter notebooks directory"
    )
    REPORTS_DIR: str = Field(
        default="./reports", description="Reports output directory"
    )
    NB_RENDER_DIR: str = Field(
        default="./reports/notebooks_html",
        description="Rendered notebooks output directory",
    )

    # Backward compatibility fields (deprecated)
    api_title: str = Field(
        default="PCS‑HELIO MCP API", description="API title (deprecated)"
    )
    api_description: str = Field(
        default="API for PCS-HELIO Model Context Protocol operations"
    )
    api_version: str = Field(default="1.0.0")
    repo_url: str = Field(default="https://github.com/agourakis82/pcs-meta-repo")
    cors_enabled: bool = Field(default=False)
    cors_origins: list[str] = Field(default_factory=list)
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    chroma_host: str = Field(default="localhost", description="Chroma host")
    chroma_port: int = Field(default=8000, description="Chroma port")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json|text)")

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        # Create directories if they don't exist
        for path_str in [
            self.DATA_DIR,
            str(Path(self.CHROMA_PATH).parent),
            self.NOTEBOOK_DIR,
            self.REPORTS_DIR,
            self.NB_RENDER_DIR,
            str(Path(self.DATA_DIR) / "ag5"),
            str(Path(self.DATA_DIR) / "helio"),
            "./static",
        ]:
            Path(path_str).mkdir(parents=True, exist_ok=True)

    # Computed properties for Path objects
    @property
    def data_path(self) -> Path:
        """Get data path as Path object."""
        return Path(self.DATA_DIR)

    @property
    def chroma_path(self) -> Path:
        """Get chroma path as Path object."""
        return Path(self.CHROMA_PATH)

    @property
    def notebook_path(self) -> Path:
        """Get notebook path as Path object."""
        return Path(self.NOTEBOOK_DIR)

    @property
    def reports_path(self) -> Path:
        """Get reports path as Path object."""
        return Path(self.REPORTS_DIR)

    @property
    def nb_render_path(self) -> Path:
        """Get notebook render path as Path object."""
        return Path(self.NB_RENDER_DIR)

    @property
    def static_path(self) -> Path:
        """Get static path as Path object."""
        return Path("./static")

    @property
    def ag5_data_path(self) -> Path:
        """Get AG5 data path as Path object."""
        return self.data_path / "ag5"

    @property
    def helio_data_path(self) -> Path:
        """Get HELIO data path as Path object."""
        return self.data_path / "helio"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENV.lower() in ("development", "dev", "debug")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENV.lower() in ("production", "prod")

    @property
    def api_keys_list(self) -> list[str]:
        """Get list of valid API keys."""
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]

    @property
    def rate_limit_requests(self) -> int:
        """Get rate limit requests (backward compatibility)."""
        return self.RATE_LIMIT_REQUESTS_PER_MINUTE

    @property
    def rate_limit_burst_size(self) -> int:
        """Get rate limit burst size (backward compatibility)."""
        return self.RATE_LIMIT_BURST_CAPACITY

    @property
    def rate_limit_window(self) -> int:
        """Get rate limit window (backward compatibility)."""
        return 60  # 1 minute window

    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key (backward compatibility)."""
        return self.OPENAI_API_KEY

    @property
    def embedding_model(self) -> str:
        """Get embedding model (backward compatibility)."""
        return self.EMBEDDING_MODEL


# Global settings instance
settings = Settings()
