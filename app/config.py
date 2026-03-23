from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    model_vendor: str = Field(default="openrouter")

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4.5"

    volcengine_api_key: str | None = None
    volcengine_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcengine_model: str = "doubao-seed-1-6-250615"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1"

    planner_temperature: float = 0.1
    worker_temperature: float = 0.2
    synthesizer_temperature: float = 0.2
    cors_allow_origins: str = "*"
    auth_secret_key: str = "local-dev-auth-secret"
    data_dir: Path = Path(".multi_agent_data")
    sqlite_path: Path = Path(".multi_agent_data/runs.db")
    coordination_dir: Path = Path("APP_DEMO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
