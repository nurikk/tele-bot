import logging

from aiogram import Dispatcher, Bot, Router, F
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Message
from openai import AsyncOpenAI

from src import db
from src.card_actions import CardActionCallback, Action
from src.card_gen import generate_cards
from src.commands import generate_broadcast
from src.db import user_from_message
from src.image_generator import ImageGenerator
from src.img import Proxy
from src.message_handlers.card import deliver_generated_samples_to_user
from src.s3 import S3Uploader
from src.settings import Settings


async def broadcast_command_handler(message: Message,
                                    image_generator: ImageGenerator,
                                    s3_uploader: S3Uploader,
                                    async_openai_client: AsyncOpenAI,
                                    bot: Bot,
                                    settings: Settings,
                                    image_proxy: Proxy) -> None:
    user = await user_from_message(telegram_user=message.from_user)
    if user.is_admin:
        await message.answer("Generating broadcast cards...")
        await generate_cards(image_generator=image_generator,
                             s3_uploader=s3_uploader,
                             async_openai_client=async_openai_client,
                             bot=bot,
                             debug_chat_id=settings.debug_chat_id,
                             image_proxy=image_proxy
                             )


async def broadcast_handler(message: Message,
                            callback_data: CardActionCallback,
                            bot: Bot,
                            image_proxy: Proxy,
                            s3_uploader: S3Uploader) -> None:
    user = await user_from_message(telegram_user=message.from_user)
    if user.is_admin:
        await message.answer("Broadcasting cards...")
        card_request = await db.CardRequests.get(id=callback_data.request_id).prefetch_related("answers")
        locale = card_request.answers[0].language_code

        user_ids = await db.get_user_ids_for_locale(locale=locale)
        recipients = await db.TelebotUsers.filter(id__in=user_ids).all()
        for recipient in recipients:
            logging.info(f'Sending card to {recipient.full_name} {recipient.id} {recipient.telegram_id}')
            try:
                await deliver_generated_samples_to_user(
                    request_id=callback_data.request_id,
                    user=recipient,
                    locale=locale,
                    debug_chat_id=None,
                    s3_uploader=s3_uploader,
                    image_proxy=image_proxy,
                    bot=bot
                )
            except TelegramForbiddenError as ex:
                logging.error(str(ex))
                await db.TelebotUsers.filter(id=recipient.id).update(is_stopped=True)


def register(dp: Dispatcher):
    form_router = Router()
    form_router.message(generate_broadcast)(broadcast_command_handler)
    form_router.callback_query(CardActionCallback.filter(F.action == Action.ACTION_BROADCAST))(broadcast_handler)
    dp.include_router(form_router)
