from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = ""
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    ollama_api_key: str = "ollama"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_port: int = 11434
    docling_serve_url: str = "http://localhost:5001"
    docling_timeout_seconds: float = 60.0
    notion_api_key: str = ""
    notion_api_base_url: str = "https://api.notion.com/v1"
    notion_api_version: str = "2022-06-28"
    notion_timeout_seconds: float = 30.0
    notion_max_items: int = 3
    session_store_path: str = ".data/estimator-sessions.json"
    llm_provider: str = "openai"  # openai | anthropic
    llm_model: str = ""
    app_env: str = "development"
    log_level: str = "info"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
