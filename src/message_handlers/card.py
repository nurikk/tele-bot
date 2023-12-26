import base64
import json
import logging
from enum import Enum

import i18n
from aiogram import types, Router, Bot, Dispatcher, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import BufferedInputFile, CallbackQuery, InputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types.base import MutableTelegramObject
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


def get_samples(key: str, locale: str) -> list[str]:
    return i18n.t(f"card_form.{key}.samples", locale=locale).split(",")


def generate_samples_keyboard(samples: list[str], columns: int = 2) -> ReplyKeyboardMarkup:
    keyboard = []
    for pair in zip(*[iter(samples)] * columns):
        keyboard.append([KeyboardButton(text=sample) for sample in pair])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_answer_samples_keyboard(locale: str, state_key: str, columns: int = 2) -> ReplyKeyboardMarkup:
    samples = get_samples(key=state_key, locale=locale)
    return generate_samples_keyboard(samples=samples, columns=columns)


async def generate_depictions_samples_keyboard(locale: str, reason: str, relationship: str, description: str) -> ReplyKeyboardMarkup:
    prompt = i18n.t("card_form.depiction.depiction_prompt", locale=locale, reason=reason, relationship=relationship, description=description)
    stream = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system",
             "content": "You are a AI designed for postcard depiction ideas generation. You have to give five short funny ideas for a depiction. Don't add any details, just two short ideas. Don't add numerals or headings. Format output as a valid json array. Produce ideas in the same language as the prompt."},
            {"role": "user", "content": prompt}
        ]
    )
    samples = []
    try:
        samples = json.loads(stream.choices[0].message.content)
    except json.decoder.JSONDecodeError:
        pass
    return generate_samples_keyboard(samples=samples, columns=1)


async def generate_descriptions_samples_keyboard(user: User, locale: str) -> MutableTelegramObject:
    requests = await CardRequest.objects.filter(user=user).filter(language_code=locale).order_by("-created_at").limit(5).all()
    descriptions = [request.request['description'] for request in requests]
    if descriptions:
        return generate_samples_keyboard(samples=descriptions, columns=1)
    return ReplyKeyboardRemove()


def register(dp: Dispatcher):
    form_router = Router()

    @form_router.message(card_command)
    async def command_start(message: types.Message, state: FSMContext) -> None:
        locale = message.from_user.language_code
        await state.set_state(CardForm.reason)
        await message.answer(i18n.t("card_form.reason.response", locale=locale),
                             reply_markup=generate_answer_samples_keyboard(locale=locale, state_key='reason', columns=1))

    @form_router.message(CardForm.reason)
    async def process_reason(message: types.Message, state: FSMContext) -> None:
        locale = message.from_user.language_code
        await state.update_data(reason=message.text)
        await state.set_state(CardForm.relationship)
        await message.answer(i18n.t("card_form.relationship.response", locale=locale),
                             reply_markup=generate_answer_samples_keyboard(locale=locale, state_key='relationship'))

    @form_router.message(CardForm.relationship)
    async def process_relationship(message: types.Message, state: FSMContext) -> None:
        locale = message.from_user.language_code
        user = await user_from_message(user=message.from_user)

        await state.update_data(relationship=message.text)
        await state.set_state(CardForm.description)

        description_ideas = await generate_descriptions_samples_keyboard(user=user, locale=locale)
        await message.answer(i18n.t("card_form.description.response", locale=locale), reply_markup=description_ideas)

    @form_router.message(CardForm.description)
    async def process_description(message: types.Message, state: FSMContext) -> None:
        locale = message.from_user.language_code
        await state.update_data(description=message.text)
        await state.set_state(CardForm.depiction)
        data = await state.get_data()

        await message.answer(i18n.t("card_form.depiction.coming_up_with_ideas", locale=locale), reply_markup=ReplyKeyboardRemove())
        # query open ai for a depiction ideas
        depiction_ideas = await generate_depictions_samples_keyboard(locale=locale, reason=data['reason'], relationship=data['relationship'],
                                                                     description=data['description'])
        await message.answer(i18n.t("card_form.depiction.response", locale=locale), reply_markup=depiction_ideas)

    @form_router.message(CardForm.depiction)
    async def process_depiction(message: types.Message, state: FSMContext) -> None:
        locale = message.from_user.language_code
        await state.update_data(depiction=message.text)
        await state.set_state(CardForm.style)

        await message.answer(i18n.t("card_form.style.response", locale=locale),
                             reply_markup=generate_answer_samples_keyboard(locale=locale, state_key='style'))

    @form_router.message(CardForm.style)
    async def process_style(message: types.Message, state: FSMContext, bot: Bot) -> None:
        locale = message.from_user.language_code
        user = await user_from_message(user=message.from_user)
        await state.update_data(style=message.text)
        await state.set_state(CardForm.style)
        await message.answer(i18n.t("card_form.wait.response", locale=locale), reply_markup=ReplyKeyboardRemove())
        data = await state.get_data()
        await state.clear()
        await finish(message=message, data=data, bot=bot, user=user, locale=locale)

    @form_router.callback_query(CardGenerationCallback.filter(F.action == Action.ACTION_REGENERATE))
    async def regenerate(query: CallbackQuery, callback_data: CardGenerationCallback, bot: Bot):
        user = await user_from_message(user=query.from_user)
        request = await CardRequest.objects.get(id=callback_data.request_id)
        await query.message.answer(i18n.t("card_form.wait.response", locale=request.language_code))
        await finish(message=query.message, data=request.request, bot=bot, user=user, locale=request.language_code)

    dp.include_router(form_router)
