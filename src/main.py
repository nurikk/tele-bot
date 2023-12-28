import asyncio
import logging
import sys
import pathlib
from datetime import timedelta

import i18n

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from src.db import start
from src.settings import settings
from src.message_handlers.start import register as register_start_handler
from src.message_handlers.card import register as register_card_handler
from src.message_handlers.img import register as register_img_handler
from src.oai import client as async_openai_client


async def main(dispatcher: Dispatcher) -> None:
    # # I18nMiddleware() i18n
    await start()

    register_start_handler(dispatcher)
    register_img_handler(dispatcher)
    register_card_handler(dispatcher)

    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    await dispatcher.start_polling(bot)


def init_i18n():
    i18n.set('skip_locale_root_data', True)
    i18n.set('filename_format', '{locale}.{format}')
    i18n.load_path.append((pathlib.Path(__file__).parent / 'translations'))


if __name__ == "__main__":
    init_i18n()
    storage = RedisStorage.from_url(settings.redis_url, state_ttl=timedelta(days=settings.redis_ttl_days))
    dp = Dispatcher(storage=storage, async_openai_client=async_openai_client)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main(dispatcher=dp))
