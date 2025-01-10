from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_token: str
    """Telegram bot token."""

    tracking_timeout: int | float = 15
    """Tracking timeout, in seconds."""

    proxy_url: Optional[str] = None
    """Proxy URL to use for opening the tracking website."""

    developer_chat_id: Optional[str] = None
    """Developer chat ID for error notifications."""

    class Config:
        env_file = ".env"
        frozen = True
        str_strip_whitespace = True


settings = Settings()  # type: ignore [call-arg]
