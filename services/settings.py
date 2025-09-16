"""
Darwin Platform Settings

Pydantic-based configuration management for the Darwin RAG + Tree-Search platform.
Loads settings from environment variables with proper validation.
"""

import os
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DarwinSettings(BaseSettings):
    """Darwin platform configuration settings."""

    model_config = SettingsConfigDict(extra="ignore")

    # Core GCP settings
    GCP_PROJECT: str = Field(default="local-development", description="GCP project ID")
    PROJECT_ID: str = Field(
        default="local-development", description="Project ID (alias)"
    )
    LOCATION: str = Field(default="us-central1", description="GCP location")

    # RAG Settings
    RAG_CORPUS: str = Field(default="", description="RAG corpus name")
    RAG_ENGINE_ENABLED: bool = Field(default=True, description="Enable RAG Engine")
    VECTOR_SEARCH_ENABLED: bool = Field(
        default=True, description="Enable Vector Search"
    )

    # RAG++ Enhanced Research Agent Settings
    RAG_PLUS_ENABLED: bool = Field(
        default=True, description="Enable RAG++ Enhanced Research Agent"
    )
    RAG_PLUS_PROJECT_ID: str = Field(
        default="local-development", description="RAG++ BigQuery project ID"
    )
    RAG_PLUS_DATASET_ID: str = Field(
        default="rag_plus_kb", description="RAG++ BigQuery dataset ID"
    )
    RAG_PLUS_TABLE_ID: str = Field(
        default="knowledge_base", description="RAG++ BigQuery table ID"
    )
    RAG_PLUS_EMBEDDING_MODEL: str = Field(
        default="textembedding-gecko@003", description="RAG++ embedding model"
    )
    RAG_PLUS_GENERATION_MODEL: str = Field(
        default="text-bison@002", description="RAG++ text generation model"
    )
    RAG_PLUS_NOVELTY_THRESHOLD: float = Field(
        default=0.8, description="RAG++ novelty detection threshold"
    )
    RAG_PLUS_MAX_ITERATIONS: int = Field(
        default=5, description="RAG++ max iterative reasoning steps"
    )
    RAG_PLUS_TOP_K_RETRIEVAL: int = Field(
        default=10, description="RAG++ top-k document retrieval"
    )
    RAG_PLUS_DISCOVERY_ENABLED: bool = Field(
        default=True, description="Enable RAG++ scientific discovery monitoring"
    )
    RAG_PLUS_DISCOVERY_INTERVAL: int = Field(
        default=3600, description="RAG++ discovery check interval (seconds)"
    )
    RAG_PLUS_RSS_FEEDS: str = Field(
        default="arxiv_cs,nature,sciencedaily",
        description="Comma-separated list of RSS feeds for discovery",
    )

    @computed_field
    @property
    def RAG_PLUS_RSS_FEEDS_LIST(self) -> List[str]:
        """Parses the comma-separated RSS feeds into a list."""
        if not self.RAG_PLUS_RSS_FEEDS:
            return []
        return [
            feed.strip() for feed in self.RAG_PLUS_RSS_FEEDS.split(",") if feed.strip()
        ]

    # Vector Search settings
    VS_INDEX_ENDPOINT: Optional[str] = Field(
        default=None, description="Vector Search index endpoint"
    )
    VS_DEPLOYED_INDEX_ID: Optional[str] = Field(
        default=None, description="Vector Search deployed index ID"
    )
    # Gemini Models
    GEMINI_EMBED_MODEL: str = Field(
        default="textembedding-gecko@003", description="Gemini embedding model"
    )
    GEMINI_ANSWER_MODEL: str = Field(
        default="gemini-1.5-pro-002", description="Gemini answer generation model"
    )

    # Security
    API_KEY_REQUIRED: bool = Field(
        default=True, description="Require API key authentication"
    )
    # Load API_KEYS as a simple string from the environment variable
    API_KEYS_STR: str = Field(
        default="",
        alias="API_KEYS",
        description="Comma-separated string of valid API keys from environment",
    )

    @computed_field
    @property
    def API_KEYS(self) -> List[str]:
        """Parses the comma-separated API_KEYS_STR into a list of strings."""
        if not self.API_KEYS_STR:
            return []
        return [key.strip() for key in self.API_KEYS_STR.split(",") if key.strip()]

    # Rate Limiting
    RATE_LIMIT_PER_MIN: int = Field(
        default=60, description="Rate limit per minute per IP"
    )
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst capacity")
    RATE_LIMIT_REQUESTS: int = Field(
        default=60, description="Requests per minute limit"
    )
    RATE_LIMIT_TOKENS: int = Field(default=10, description="Tokens per request limit")

    # External integrations
    BASE_URL: str = Field(
        default="http://localhost:8000", description="Base URL for the service"
    )
    OPENAI_VERIFICATION_TOKEN: str = Field(
        default="", description="OpenAI verification token"
    )

    # Cache Configuration
    RAG_CACHE_TTL: int = Field(default=3600, description="RAG cache TTL in seconds")
    RAG_CACHE_SIZE: int = Field(default=1000, description="RAG cache max size")

    # Tree Search Configuration
    TS_MAX_BUDGET_NODES: int = Field(default=300, description="Max TS budget nodes")
    TS_MAX_DEPTH: int = Field(default=5, description="Max TS depth")
    TS_DEFAULT_BUDGET: int = Field(default=150, description="Default TS budget")

    # Context Caching
    CONTEXT_CACHE_ENABLED: bool = Field(
        default=True, description="Enable context caching"
    )

    # Application
    APP_NAME: str = Field(default="Darwin", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")


def _load_secrets_and_get_settings() -> DarwinSettings:
    """
    Load secrets from Google Secret Manager into environment variables
    BEFORE initializing the settings. This ensures env vars are available
    for Pydantic to read.
    """
    # Default to local-development if GCP_PROJECT is not set
    project_id = os.environ.get("GCP_PROJECT", "local-development")

    # Only attempt to load secrets if not in local development
    if project_id != "local-development":
        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()
            project_path = f"projects/{project_id}"

            secret_names = [
                "OPENAI_API_KEY",
                "GEMINI_API_KEY",
                "API_KEYS",
                "RAG_CORPUS",
                "VS_INDEX_ENDPOINT",
                "VS_DEPLOYED_INDEX_ID",
                # RAG++ specific secrets
                "RAG_PLUS_PROJECT_ID",
                "RAG_PLUS_DATASET_ID",
                "RAG_PLUS_TABLE_ID",
                "RAG_PLUS_RSS_FEEDS",
            ]

            for secret_name in secret_names:
                try:
                    secret_path = (
                        f"{project_path}/secrets/{secret_name}/versions/latest"
                    )
                    response = client.access_secret_version(
                        request={"name": secret_path}
                    )
                    # Set the secret value as an environment variable
                    os.environ[secret_name] = response.payload.data.decode("utf-8")
                except Exception:
                    # Secret might not exist, which can be okay.
                    pass

        except (ImportError, Exception) as e:
            # This might happen in local environments without gcloud libs.
            print(f"Warning: Could not load secrets from Secret Manager: {e}")

    # Initialize settings AFTER environment variables have been populated
    return DarwinSettings()


# --- Global Settings Instance ---
# This function is called once on module load to create the global 'settings' object.
settings = _load_secrets_and_get_settings()


def get_settings() -> DarwinSettings:
    """Returns the globally shared settings instance."""
    return settings
