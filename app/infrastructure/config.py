"""Application configuration via environment variables / .env."""
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./novel_ignite.db"
    model_base_url: str = ""
    model_api_key: str = ""
    model_name: str = ""
    model_provider: str = "fake"
    model_timeout: int = 300
    agnes_api_key: str = ""
    deepseek_api_key: str = ""
    grok_api_key: str = ""

    model_config = ConfigDict(env_file=".env", extra="allow")


settings = Settings()
