import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    openai_api_key: str
    # Bot token can be obtained via https://t.me/BotFather
    telegram_bot_token: str


settings = Settings()
