import i18n
from aiogram import Dispatcher, types, Bot
from aiogram.filters import CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.commands import start_command, start_referral_command, stop_command, generate_broadcast
from src.db import user_from_message, TelebotUsers
from src.settings import Settings


def register(dp: Dispatcher):
    @dp.message(generate_broadcast)
    async def broadcast_command_handler(message: Message) -> None:
        user = await user_from_message(telegram_user=message.from_user)

        # await TelebotUsers.filter(telegram_id=message.from_user.id).update(is_stopped=True)
        # await message.answer(i18n.t('stop_message', locale=message.from_user.language_code, name=hbold(message.from_user.full_name)))
