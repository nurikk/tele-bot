import i18n
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.commands import stop_command
from src.db import TelebotUsers


def register(dp: Dispatcher):
    @dp.message(stop_command)
    async def stop_command_handler(message: Message) -> None:
        await TelebotUsers.filter(telegram_id=message.from_user.id).update(
            is_stopped=True
        )
        await message.answer(
            i18n.t(
                "stop_message",
                locale=message.from_user.language_code,
                name=hbold(message.from_user.full_name),
            )
        )
