import asyncio
import logging
import sys
import pathlib

import i18n


from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from src.db import start
from src.settings import settings
from src.message_handlers.start import register as register_start_handler
from src.message_handlers.card import register as register_card_handler
from src.message_handlers.img import register as register_img_handler


async def main(dispatcher: Dispatcher) -> None:
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
    dp = Dispatcher()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main(dispatcher=dp))
