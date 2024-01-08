import pytest
from aiogram import Bot
from aiogram.enums import ParseMode
from openai import AsyncOpenAI

from src import card_gen
from src.image_generator import ReplicateGenerator
from src.img import ImageOptim
from src.main import init_i18n
from src.s3 import S3Uploader


@pytest.mark.asyncio
async def test_generate_cards(db_mock, settings):
    init_i18n()
    image_generator = ReplicateGenerator(api_token=settings.replicate_api_token)
    async_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    s3_uploader = S3Uploader(aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key,
                             aws_region=settings.aws_region, s3_bucket_name=settings.s3_bucket_name)

    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)

    await card_gen.generate_cards(image_generator=image_generator,
                                  async_openai_client=async_openai_client, s3_uploader=s3_uploader, bot=bot,
                                  image_proxy=ImageOptim(account_id=settings.imageoptim_account_id),
                                  debug_chat_id=settings.debug_chat_id,
                                  cards_per_holiday=2)
