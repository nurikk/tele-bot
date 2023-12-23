import pydantic_settings
from pydantic_settings import SettingsConfigDict


class Settings(pydantic_settings.BaseSettings):
    debug_chat_id: int = -4028365371
    db_url: str = 'postgresql+asyncpg://localhost:5432/telebot'

    openai_api_key: str = ''  # Bot token can be obtained via https://t.me/BotFather
    telegram_bot_token: str = ''

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
