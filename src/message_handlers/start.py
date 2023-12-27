import i18n
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.commands import start_command
from src.db import TelebotUsers, user_from_message


def register(dp: Dispatcher):
    @dp.message(start_command)
    async def handler(message: Message) -> None:
        await user_from_message(telegram_user=message.from_user)

        welcome_messages = [
            i18n.t('first_message', name=hbold(message.from_user.full_name), locale=message.from_user.language_code),
            i18n.t('commands.card', locale=message.from_user.language_code)
        ]
        await message.answer("\n".join(welcome_messages))
