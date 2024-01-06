import pydantic_settings
from pydantic_settings import SettingsConfigDict


class Settings(pydantic_settings.BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    debug_chat_id: int = -4028365371
    db_url: str = 'postgres://localhost:5432/telebot2'
    redis_url: str = 'redis://localhost:6379/0'
    redis_ttl_days: int = 1
    cards_per_user: int = 5

    openai_api_key: str = ''  # Bot token can be obtained via https://t.me/BotFather
    telegram_bot_token: str = ''

    aws_access_key_id: str = ''
    aws_secret_access_key: str = ''
    s3_bucket_name: str = ''
    aws_region: str = ''

    imageoptim_account_id: str = ''

    image_website_prefix: str = ''
    image_thumbnail_website_prefix: str = ''

    imgproxy_hostname: str = ''
    imgproxy_port: str = '8080'
    imgproxy_key: str = ''
    imgproxy_salt: str = ''

    replicate_api_token: str = ''
