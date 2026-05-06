from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    reports_dir: Path = Path("../.sphere/workflows/output")
    sih_command: Path = Path.home() / ".dotnet/tools/sih"

    model_config = SettingsConfigDict(env_prefix="SIH_SMART_", env_file=".env")


def get_settings() -> Settings:
    return Settings()
