"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized settings loaded from environment / .env file."""

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_temperature_structured: float = 0.0
    llm_temperature_creative: float = 0.3
    llm_max_retries: int = 3

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "sqlite:///./app.db"

    # Limits
    max_upload_size_mb: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
