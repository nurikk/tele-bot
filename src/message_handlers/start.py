import i18n
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.commands import start_command


def register(dp: Dispatcher):
    @dp.message(start_command)
    async def handler(message: Message) -> None:
        """
        This handler receives messages with `/start` command
        """
        # Most event objects have aliases for API methods that can be called in events' context
        # For example if you want to answer to incoming message you can use `message.answer(...)` alias
        # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
        # method automatically or call API method directly via
        # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
        welcome_messages = [
            i18n.t('first_message', name=hbold(message.from_user.full_name), locale=message.from_user.language_code),
            i18n.t('commands.card', locale=message.from_user.language_code)
        ]
        await message.answer("\n".join(welcome_messages))
