import pydantic_settings
from pydantic_settings import SettingsConfigDict


class Settings(pydantic_settings.BaseSettings):
    openai_api_key: str = '' # Bot token can be obtained via https://t.me/BotFather
    telegram_bot_token: str = ''

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
