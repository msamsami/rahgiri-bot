from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_token: str
    developer_chat_id: str

    class Config:
        env_file = ".env"
        frozen = True
        str_strip_whitespace = True


settings = Settings()  # type: ignore [call-arg]
