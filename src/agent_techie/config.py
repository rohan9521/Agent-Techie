from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    llm_provider: str | None = "ollama"
    model_name: str = "qwen2.5-coder"
    openai_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    ollama_base_url: str = "http://localhost:11434"
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str | None = None
    langsmith_project: str = "agent-techie"
    workspace_root: str = "."
    max_workflow_iterations: int = 20
    github_token: str | None = None
    persistence_backend: str = "memory"
    database_url: str | None = None
    redis_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
