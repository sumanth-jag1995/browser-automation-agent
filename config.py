"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    redis_url: str = "redis://localhost:6379/0"
    max_retries: int = 3
    use_mock_llm: bool = False
    screenshot_dir: Path = Path("screenshots/current")
    baseline_dir: Path = Path("screenshots/baseline")
    reports_dir: Path = Path("reports")
    scripts_dir: Path = Path("scripts")
    max_repair_before_regenerate: int = 2
    playwright_headless: bool = True
    log_level: str = "INFO"
    langsmith_api_key: str = ""
    langsmith_project: str = "browser-automation-agent"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_api_key) and not self.use_mock_llm


@lru_cache
def get_settings() -> Settings:
    return Settings()
