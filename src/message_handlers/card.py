import base64
import json
from enum import Enum

import i18n
from aiogram import types, Router, Bot, Dispatcher, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hcode, hbold, hpre
from openai import BadRequestError, AsyncOpenAI
from tortoise.expressions import F as F_SQL
from tortoise.functions import Max

from src.commands import card_command
from src.db import user_from_message, TelebotUsers, CardRequests, CardRequestQuestions, CardRequestsAnswers
from src.fsm.card import CardForm

from src.prompt_generator import generate_prompt
from src.settings import settings


async def debug_log(prompt_data: dict, bot: Bot, prompt: str, revised_prompt: str, image: BufferedInputFile, user: TelebotUsers):
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


async def generate_image(client: AsyncOpenAI, prompt: str, user_id: str) -> (InputFile, str):
    response = await client.images.generate(prompt=prompt, model="dall-e-3", response_format="b64_json", user=user_id)
    img = response.data[0]  # Api only returns one image
    # TODO: save images to s3
    return BufferedInputFile(file=base64.b64decode(img.b64_json), filename="card.png"), img.revised_prompt


def generate_image_keyboad(locale: str, request_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    button_label = i18n.t('regenerate', locale=locale)
    callback_data = CardGenerationCallback(
        action=Action.ACTION_REGENERATE, request_id=request_id).pack()
    builder.button(text=button_label, callback_data=callback_data)
    return builder


async def finish(chat_id: int, request_id: int, bot: Bot, user: TelebotUsers, locale: str, client: AsyncOpenAI) -> None:
    answers = await CardRequestsAnswers.filter(request_id=request_id).all().values()
    data = {item['question'].value: item['answer'] for item in answers}
    prompt = generate_prompt(data=data, locale=locale)
    await CardRequests.filter(id=request_id).update(generated_prompt=prompt)

    try:
        image, revised_prompt = await generate_image(prompt=prompt, user_id=str(user.id), client=client)
        keyboard = generate_image_keyboad(locale=locale, request_id=request_id)

        await TelebotUsers.filter(id=user.id).update(remaining_cards=F_SQL("remaining_cards") - 1)

        await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=keyboard.as_markup())

        await bot.send_message(chat_id=chat_id, text=i18n.t('commands.card', locale=locale))

        await CardRequests.filter(id=request_id).update(revised_prompt=revised_prompt)
        await debug_log(prompt_data=data, bot=bot, prompt=prompt,
                        revised_prompt=revised_prompt, image=image, user=user)
    except BadRequestError as e:
        if isinstance(e.body, dict) and 'message' in e.body:
            await bot.send_message(chat_id=chat_id, text=e.body['message'])


def get_samples(question: CardRequestQuestions, locale: str) -> list[str]:
    return i18n.t(f"card_form.{question.value}.samples", locale=locale).split(",")


def generate_samples_keyboard(samples: list[str], columns: int = 2) -> ReplyKeyboardMarkup:
    keyboard = []
    for pair in zip(*[iter(samples)] * columns):
        keyboard.append([KeyboardButton(text=sample) for sample in pair])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_answer_samples_keyboard(locale: str, question: CardRequestQuestions, columns: int = 2) -> ReplyKeyboardMarkup:
    samples = get_samples(question=question, locale=locale)
    return generate_samples_keyboard(samples=samples, columns=columns)


async def generate_depictions_samples_keyboard(client: AsyncOpenAI, locale: str, request_id: int) -> ReplyKeyboardMarkup:
    answers = await CardRequests.filter(id=request_id,
                                        answers__language_code=locale,
                                        answers__question__in=[CardRequestQuestions.DESCRIPTION, CardRequestQuestions.REASON,
                                                               CardRequestQuestions.RELATIONSHIP]
                                        ).values('answers__question', 'answers__answer')

    answers_dict = {item['answers__question']: item['answers__answer'] for item in answers}

    prompt = i18n.t("card_form.depiction.depiction_prompt", locale=locale,
                    reason=answers_dict[CardRequestQuestions.REASON],
                    relationship=answers_dict[CardRequestQuestions.RELATIONSHIP],
                    description=answers_dict[CardRequestQuestions.DESCRIPTION])
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


async def generate_descriptions_samples_keyboard(user: TelebotUsers, locale: str, samples_count: int = 5):
    # Refactor this to make DISTINCT ON query
    answers = await CardRequests.filter(user=user,
                                        answers__language_code=locale,
                                        answers__question=CardRequestQuestions.DESCRIPTION
                                        ).annotate(min_created_at=Max('created_at')).order_by("-min_created_at").group_by('answers__answer').limit(
        samples_count).values("answers__answer")

    descriptions = [answer['answers__answer'] for answer in answers]
    if descriptions:
        return generate_samples_keyboard(samples=descriptions, columns=1)
    return ReplyKeyboardRemove()


async def handle_no_more_cards(message: types.Message):
    locale = message.from_user.language_code
    await message.answer(i18n.t("card_form.no_cards_left", locale=locale))

    kb = [[
        InlineKeyboardButton(
            text="Выбрать ссылку",
            switch_inline_query_current_chat="links"
        )
    ], [
        InlineKeyboardButton(
            text="Выбрать изображение",
            switch_inline_query_current_chat="images"
        )
    ]]
    await message.answer(
        text="Выберите, что хотите удалить:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


async def command_start(message: types.Message, state: FSMContext) -> None:
    locale = message.from_user.language_code
    user = await user_from_message(telegram_user=message.from_user)
    if user.remaining_cards <= 0:
        await handle_no_more_cards(message=message)
    else:
        request: CardRequests = await CardRequests.create(user=user, language_code=locale)
        await state.update_data(request_id=request.id)
        await state.set_state(CardForm.reason)
        answer_samples_keyboard = generate_answer_samples_keyboard(locale=locale, question=CardRequestQuestions.REASON, columns=1)
        await message.answer(i18n.t("card_form.reason.response", locale=locale), reply_markup=answer_samples_keyboard)


async def process_reason(message: types.Message, state: FSMContext) -> None:
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.REASON, answer=message.text, language_code=locale)
    await state.set_state(CardForm.relationship)
    answer_samples_keyboard = generate_answer_samples_keyboard(locale=locale, question=CardRequestQuestions.RELATIONSHIP)
    await message.answer(i18n.t("card_form.relationship.response", locale=locale), reply_markup=answer_samples_keyboard)


async def process_description(message: types.Message, state: FSMContext, async_openai_client: AsyncOpenAI) -> None:
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.DESCRIPTION, answer=message.text, language_code=locale)
    await state.set_state(CardForm.depiction)

    await message.answer(i18n.t("card_form.depiction.coming_up_with_ideas", locale=locale), reply_markup=ReplyKeyboardRemove())
    depiction_ideas = await generate_depictions_samples_keyboard(locale=locale, request_id=request_id, client=async_openai_client)
    await message.answer(i18n.t("card_form.depiction.response", locale=locale), reply_markup=depiction_ideas)


async def process_depiction(message: types.Message, state: FSMContext) -> None:
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.DEPICTION, answer=message.text, language_code=locale)
    await state.set_state(CardForm.style)

    await message.answer(i18n.t("card_form.style.response", locale=locale),
                         reply_markup=generate_answer_samples_keyboard(locale=locale, question=CardRequestQuestions.STYLE))


async def process_style(message: types.Message, state: FSMContext, bot: Bot, async_openai_client: AsyncOpenAI) -> None:
    locale = message.from_user.language_code
    user = await user_from_message(telegram_user=message.from_user)
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.STYLE, answer=message.text, language_code=locale)
    await state.set_state(CardForm.style)
    await message.answer(i18n.t("card_form.wait.response", locale=locale), reply_markup=ReplyKeyboardRemove())
    await state.clear()
    await finish(chat_id=message.chat.id, request_id=request_id, bot=bot, user=user, locale=locale, client=async_openai_client)


async def process_relationship(message: types.Message, state: FSMContext) -> None:
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.RELATIONSHIP, answer=message.text, language_code=locale)
    user = await user_from_message(telegram_user=message.from_user)
    await state.set_state(CardForm.description)

    description_ideas = await generate_descriptions_samples_keyboard(user=user, locale=locale)
    await message.answer(i18n.t("card_form.description.response", locale=locale), reply_markup=description_ideas)


async def regenerate(query: CallbackQuery, callback_data: CardGenerationCallback, bot: Bot, async_openai_client: AsyncOpenAI):
    user = await user_from_message(telegram_user=query.from_user)
    locale = query.from_user.language_code
    await query.message.answer(i18n.t("card_form.wait.response", locale=locale))
    await finish(chat_id=query.message.chat.id, request_id=callback_data.request_id, bot=bot, user=user, locale=locale,
                 client=async_openai_client)


def register(dp: Dispatcher):
    form_router = Router()
    form_router.message(card_command)(command_start)
    form_router.message(CardForm.reason)(process_reason)
    form_router.message(CardForm.relationship)(process_relationship)
    form_router.message(CardForm.description)(process_description)
    form_router.message(CardForm.depiction)(process_depiction)
    form_router.message(CardForm.style)(process_style)
    form_router.callback_query(CardGenerationCallback.filter(F.action == Action.ACTION_REGENERATE))(regenerate)

    dp.include_router(form_router)
