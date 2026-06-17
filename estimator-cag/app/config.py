from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = ""
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
    vector_database_url: str = ""
    vector_db_initialize_on_start: bool = True
    embedding_context_model: str = "gpt-4o-mini"
    chunking_default_strategy: str = "structural"
    chunking_include_parent_context: bool = True
    chunking_max_characters: int = 900
    chunking_overlap_characters: int = 120
    chunking_enable_llm_context: bool = False
    llm_provider: str = "openai"  # openai | anthropic
    llm_model: str = ""
    app_env: str = "development"
    log_level: str = "info"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
