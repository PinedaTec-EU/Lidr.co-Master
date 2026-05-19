from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_REPORTS_DIR = Path(
    "/Users/jmr.pineda/Projects/GitHub/PinedaTec.eu/TravelAgent/.sphere/workflows/bootstrap/output"
)


class Settings(BaseSettings):
    reports_dir: Path = DEFAULT_REPORTS_DIR
    sih_command: Path = Path.home() / ".dotnet/tools/sih"
    llm_enabled: bool = True
    llm_model: str = "openai/gpt-4o-mini"
    llm_max_tokens: int = 1400

    model_config = SettingsConfigDict(env_prefix="SIH_SMART_", env_file=".env")


def get_settings() -> Settings:
    return Settings()
