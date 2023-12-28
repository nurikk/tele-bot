import i18n
from aiogram import Dispatcher, types
from aiogram.filters import CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.commands import start_command, start_referral_command
from src.db import user_from_message


async def handle_new_user(message: types.Message, referred_by: int = None):
    await user_from_message(telegram_user=message.from_user, referred_by=referred_by)

    welcome_messages = [
        i18n.t('first_message', name=hbold(message.from_user.full_name), locale=message.from_user.language_code),
        i18n.t('commands.card', locale=message.from_user.language_code)
    ]
    await message.answer("\n".join(welcome_messages))


def register(dp: Dispatcher):
    @dp.message(start_command)
    @dp.message(start_referral_command)
    async def referral(message: Message, command: CommandObject) -> None:
        referred_by = command.args
        await handle_new_user(message=message, referred_by=int(referred_by) if referred_by else None)
