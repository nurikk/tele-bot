import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from src.settings import settings
from src.message_handlers.start import register as register_start_handler
from src.message_handlers.card import register as register_card_handler
from src.message_handlers.img import register as register_img_handler


async def main(dispatcher: Dispatcher) -> None:
    register_start_handler(dispatcher)
    register_img_handler(dispatcher)
    register_card_handler(dispatcher)

    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    dp = Dispatcher()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main(dispatcher=dp))
