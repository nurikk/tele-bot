from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold


def register(dp: Dispatcher):
    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        """
        This handler receives messages with `/start` command
        """
        # Most event objects have aliases for API methods that can be called in events' context
        # For example if you want to answer to incoming message you can use `message.answer(...)` alias
        # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
        # method automatically or call API method directly via
        # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
        await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")
