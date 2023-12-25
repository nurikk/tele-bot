import base64
import json
import logging
from enum import Enum

import i18n
from aiogram import types, Router, Bot, Dispatcher, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hcode, hbold, hpre
from openai import BadRequestError

from src.commands import card_command
from src.db import user_from_message, User, CardRequest
from src.fsm.card import CardForm
from src.oai import client
from src.prompt_generator import generate_prompt
from src.settings import settings


async def debug_log(prompt_data: dict, bot: Bot, prompt: str, revised_prompt: str, image: BufferedInputFile, user: User):
    messages = [
        f"New card for {hbold(user.full_name)} @{user.username}!",
        f"User response: \n {hpre(json.dumps(prompt_data, indent=4))}",
        f"Generated prompt:\n {hcode(prompt)}",
        f"Revised prompt:\n {hcode(revised_prompt)}"
    ]
    await bot.send_message(chat_id=settings.debug_chat_id, text="\n".join(messages))
    await bot.send_photo(chat_id=settings.debug_chat_id, photo=image)


class Action(str, Enum):
    ACTION_REGENERATE = "regenerate"


class CardGenerationCallback(CallbackData, prefix="my"):
    action: Action
    request_id: int


async def generate_image(prompt: str, user_id: str) -> (InputFile, str):
    response = await client.images.generate(prompt=prompt, model="dall-e-3", response_format="b64_json", user=user_id)
    img = response.data[0]  # Api only returns one image
    # TODO: save images to s3
    return BufferedInputFile(file=base64.b64decode(img.b64_json), filename="card.png"), img.revised_prompt


def generate_image_keyboad(locale: str, request: CardRequest) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    button_label = i18n.t('regenerate', locale=locale)
    callback_data = CardGenerationCallback(
        action=Action.ACTION_REGENERATE, request_id=request.id).pack()
    builder.button(text=button_label, callback_data=callback_data)
    return builder


async def finish(message: types.Message, data: dict[str, any], bot: Bot, user: User, locale: str) -> None:

    prompt = generate_prompt(data=data, locale=locale)
    request: CardRequest = await CardRequest.objects.create(user=user,
                                                            request=data,
                                                            generated_prompt=prompt,
                                                            language_code=locale)
    try:
        image, revised_prompt = await generate_image(prompt=prompt, user_id=str(user.id))
        keyboard = generate_image_keyboad(locale=locale, request=request)
        await bot.send_photo(chat_id=message.chat.id, photo=image, reply_markup=keyboard.as_markup())

        await bot.send_message(chat_id=message.chat.id, text=i18n.t('commands.card', locale=locale))

        await request.update(revised_prompt=revised_prompt)
        await debug_log(prompt_data=data, bot=bot, prompt=prompt,
                        revised_prompt=revised_prompt, image=image, user=user)
    except BadRequestError as e:
        await message.reply(text=e.body['message'])


def generate_message_handler(form_router: Router, start_command, key: str, next_state, answer: str):
    @form_router.message(start_command)
    async def handler(message: types.Message, state: FSMContext, bot: Bot) -> None:
        user = await user_from_message(user=message.from_user)
        if key:
            logging.info(f"Updating data for {key=} {message.text=}")
            await state.update_data({key: message.text})
        if answer:
            await message.answer(i18n.t(answer, locale=message.from_user.language_code))
        if next_state:
            await state.set_state(next_state)
        else:
            data = await state.get_data()
            await state.clear()
            await finish(message=message, data=data, bot=bot, user=user, locale=message.from_user.language_code)


commands = [
    (card_command, CardForm.reason, None, "card_form.reason"),
    (CardForm.reason, CardForm.relationship, "reason", "card_form.relationship"),
    (CardForm.relationship, CardForm.description,
     "relationship", "card_form.description"),
    (CardForm.description, CardForm.depiction,
     "description", "card_form.depiction"),
    (CardForm.depiction, CardForm.style, "depiction", "card_form.style"),
    (CardForm.style, None, "style", "card_form.wait")
]


def register(dp: Dispatcher):
    form_router = Router()

    for start_command, next_state, key, question in commands:
        generate_message_handler(
            form_router, start_command, key, next_state, question)

    @form_router.callback_query(CardGenerationCallback.filter(F.action == Action.ACTION_REGENERATE))
    async def regenerate(query: CallbackQuery, callback_data: CardGenerationCallback, bot: Bot):
        user = await user_from_message(user=query.from_user)
        request = await CardRequest.objects.get(id=callback_data.request_id)
        await query.message.answer(i18n.t("card_form.wait", locale=request.language_code))
        await finish(message=query.message, data=request.request, bot=bot, user=user, locale=request.language_code)

    dp.include_router(form_router)
