from aiogram import Dispatcher, Router
from aiogram.types import Message, LinkPreviewOptions

from src import db
from src.commands import calendar
from src.db import user_from_message
from src.message_handlers.card import escape_markdown


async def calendar_command_handler(message: Message) -> None:
    await user_from_message(telegram_user=message.from_user)
    locale = message.from_user.language_code

    holidays = await db.get_near_holidays(locale, days=7)
    calendar_msg_markdown = []
    for holiday in holidays:
        calendar_msg_markdown.append(
            f"""[{escape_markdown(holiday.date.strftime("%Y-%m-%d"))} {escape_markdown(holiday.title)}]({holiday.url}) \n {escape_markdown(holiday.description)}"""
        )

    await message.reply(
        "\n\n".join(calendar_msg_markdown),
        parse_mode="MarkdownV2",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def register(dp: Dispatcher):
    form_router = Router()
    form_router.message(calendar)(calendar_command_handler)
    dp.include_router(form_router)
