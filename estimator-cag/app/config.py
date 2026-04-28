from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"  # openai | anthropic
    llm_model: str = ""
    app_env: str = "development"
    log_level: str = "info"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
