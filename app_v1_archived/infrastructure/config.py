from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./novel_ignite.db"
    # 默认生成模型提供方：fake | agnes | deepseek | grok
    model_provider: str = "fake"
    # 兼容旧单模型字段（保留，用于直接指定某一提供方时的覆盖）
    model_base_url: str | None = None
    model_api_key: str | None = None
    model_name: str = "fake-model"
    # Agnes
    agnes_base_url: str = "https://apihub.agnes-ai.com/v1"
    agnes_api_key: str | None = None
    agnes_model: str = "agnes-2.0-flash"
    # DeepSeek
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-v4-flash"
    # Grok
    grok_base_url: str = "https://modelflare.dev/v1"
    grok_api_key: str | None = None
    grok_model: str = "grok-4.5"
    # 模型调用超时（秒）；reasoning 类模型生成完整蓝图可能耗时较长
    model_timeout: float = 300.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
