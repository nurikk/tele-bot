import i18n
from aiogram import Dispatcher, types, Bot
from aiogram.filters import CommandObject
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.commands import start_command, start_referral_command
from src.db import user_from_message
from src.settings import Settings


async def handle_new_user(message: types.Message, bot: Bot, cards_per_user: int = 5,   referred_by: int = None):
    await user_from_message(telegram_user=message.from_user, referred_by=referred_by, bot=bot, cards_per_user=cards_per_user)

    welcome_messages = [
        i18n.t('first_message', name=hbold(message.from_user.full_name), locale=message.from_user.language_code),
        i18n.t('commands.card', locale=message.from_user.language_code)
    ]
    await message.answer("\n".join(welcome_messages))


def register(dp: Dispatcher):
    @dp.message(start_command)
    @dp.message(start_referral_command)
    async def start_command_handler(message: Message, command: CommandObject, bot: Bot, settings: Settings) -> None:
        referred_by = command.args
        await handle_new_user(message=message, bot=bot,
                              referred_by=int(referred_by) if referred_by else None,
                              cards_per_user=settings.cards_per_user)
