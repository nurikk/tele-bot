import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from src.settings import settings
from message_handlers.start import register as register_start_handler
from message_handlers.echo import register as register_echo_handler


async def main(dispatcher: Dispatcher) -> None:
    register_start_handler(dispatcher)
    register_echo_handler(dispatcher)

    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    dp = Dispatcher()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main(dispatcher=dp))
