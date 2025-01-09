from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_token: str
    """Telegram bot token."""

    tracking_timeout: int | float = 15
    """Tracking timeout, in seconds."""

    developer_chat_id: Optional[str] = None
    """Developer chat ID for error notifications."""

    class Config:
        env_file = ".env"
        frozen = True
        str_strip_whitespace = True


settings = Settings()  # type: ignore [call-arg]
