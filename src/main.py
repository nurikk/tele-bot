import asyncio
import logging
import pathlib
import sys
from datetime import timedelta

import i18n
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from openai import AsyncOpenAI

from src import db
from src.commands import card_bot_command, stop_bot_command, calendar_bot_command
from src.image_generator import ReplicateGenerator
from src.img import ImageOptim, ImageProxy
from src.message_handlers.broadcaster import register as register_broadcast_handler
from src.message_handlers.card import register as register_card_handler
from src.message_handlers.img import register as register_img_handler
from src.message_handlers.start import register as register_start_handler
from src.message_handlers.stop import register as register_stop_handler
from src.message_handlers.calendar import register as register_calendar_handler
from src.s3 import S3Uploader
from src.settings import Settings


async def startup(bot: Bot) -> None:
    await set_default_commands(bot)
    for locale in i18n.config.settings['available_locales']:
        await bot.set_my_description(description=i18n.t('bot_description', locale=locale), language_code=locale)
        await bot.set_my_short_description(short_description=i18n.t('bot_short_description', locale=locale), language_code=locale)

    logging.info("bot started")


async def set_default_commands(bot: Bot) -> None:
    commands = [
        card_bot_command,
        stop_bot_command,
        calendar_bot_command
    ]
    for locale in i18n.config.settings['available_locales']:
        await bot.set_my_commands(
            [
                BotCommand(command=c.command, description=i18n.t(f'bot_commands.{c.command}', locale=locale)) for c in commands
            ], language_code=locale
        )


async def main(dispatcher: Dispatcher, telegram_bot_token: str, db_url: str) -> None:
    await db.start(db_url=db_url)
    await db.load_holidays()

    register_start_handler(dispatcher)
    register_stop_handler(dispatcher)
    register_img_handler(dispatcher)
    register_card_handler(dispatcher)
    register_broadcast_handler(dispatcher)
    register_calendar_handler(dispatcher)

    bot = Bot(token=telegram_bot_token, parse_mode=ParseMode.HTML)

    dispatcher.startup.register(startup)

    await dispatcher.start_polling(bot)


def init_i18n():
    i18n.set('available_locales', ['en', 'ru'])
    i18n.set('skip_locale_root_data', True)
    i18n.set('filename_format', '{locale}.{format}')
    i18n.load_path.append((pathlib.Path(__file__).parent / 'translations'))


if __name__ == "__main__":
    init_i18n()
    settings = Settings()
    dp = Dispatcher(storage=RedisStorage.from_url(settings.redis_url, state_ttl=timedelta(days=settings.redis_ttl_days)),
                    # image_generator=OpenAIGenerator(api_key=settings.openai_api_key),
                    image_generator=ReplicateGenerator(api_token=settings.replicate_api_token),
                    async_openai_client=AsyncOpenAI(api_key=settings.openai_api_key),
                    settings=settings,
                    s3_uploader=S3Uploader(aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key,
                                           aws_region=settings.aws_region, s3_bucket_name=settings.s3_bucket_name),
                    # image_proxy=ImageOptim(account_id=settings.imageoptim_account_id),
                    image_proxy=ImageProxy(imgproxy_hostname=settings.imgproxy_hostname,
                                           imgproxy_key=settings.imgproxy_key,
                                           imgproxy_salt=settings.imgproxy_salt)
                    )
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main(dispatcher=dp, telegram_bot_token=settings.telegram_bot_token, db_url=settings.db_url))
