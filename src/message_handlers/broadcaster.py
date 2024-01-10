import logging
from collections import defaultdict

from aiogram import Dispatcher, Bot, Router, F
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Message, CallbackQuery
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
        sent_message = await message.answer("Generating broadcast cards...")
        try:
            await generate_cards(image_generator=image_generator,
                                 s3_uploader=s3_uploader,
                                 async_openai_client=async_openai_client,
                                 bot=bot,
                                 debug_chat_id=settings.debug_chat_id,
                                 image_proxy=image_proxy
                                 )
        except Exception as ex:
            logging.error(str(ex))
            await sent_message.edit_text("Error while generating cards")
            await message.answer(str(ex))


async def broadcast_handler(message: CallbackQuery,
                            callback_data: CardActionCallback,
                            bot: Bot,
                            image_proxy: Proxy,
                            s3_uploader: S3Uploader) -> None:
    user = await user_from_message(telegram_user=message.from_user)
    if user.is_admin:
        sent_message = await message.message.answer("Broadcasting cards...")
        card_request = await db.CardRequests.get(id=callback_data.request_id).prefetch_related("answers")
        locale = card_request.answers[0].language_code

        user_ids = await db.get_user_ids_for_locale(locale=locale)
        recipients = await db.TelebotUsers.filter(id__in=user_ids).all()
        total = len(recipients)
        exceptions = defaultdict(int)
        for idx, recipient in enumerate(recipients):
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
                exceptions[str(ex)] += 1
            excs = ''
            for k, v in exceptions.items():
                excs += f'{k}: {v}\n'
            await sent_message.edit_text(f"Broadcasting cards...{idx+1}/{total}\n{excs}")


def register(dp: Dispatcher):
    form_router = Router()
    form_router.message(generate_broadcast)(broadcast_command_handler)
    form_router.callback_query(CardActionCallback.filter(F.action == Action.ACTION_BROADCAST))(broadcast_handler)
    dp.include_router(form_router)
