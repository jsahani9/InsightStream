"""Application configuration.

Loads all settings from environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str

    # AWS Bedrock
    aws_region: str = "us-east-1"
    bedrock_claude_model_id: str
    bedrock_llama_model_id: str

    # OpenAI
    openai_api_key: str
    openai_planner_model: str
    openai_verifier_model: str
    openai_embedding_model: str

    # Web search
    serper_api_key: str


settings = Settings()