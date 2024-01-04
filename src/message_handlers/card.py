import base64
import datetime
import json
import logging
from enum import Enum

import i18n
from aiogram import types, Router, Bot, Dispatcher, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup, SwitchInlineQueryChosenChat, URLInputFile, InputFile
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hcode, hbold, hpre
from openai import BadRequestError, AsyncOpenAI
from openai.types import Image
from tortoise.expressions import F as F_SQL
from tortoise.functions import Max

from src.commands import card_command
from src.db import user_from_message, TelebotUsers, CardRequests, CardRequestQuestions, CardRequestsAnswers
from src.fsm.card import CardForm
from src.img import ImageProxy

from src.prompt_generator import generate_prompt
from src.s3 import S3Uploader
from src.settings import Settings


async def debug_log(prompt_data: dict, bot: Bot, prompt: str, revised_prompt: str,
                    photo: InputFile, user: TelebotUsers, debug_chat_id: int):
    messages = [
        f"New card for {hbold(user.full_name)} @{user.username}!",
        f"User response: \n {hpre(json.dumps(prompt_data, indent=4))}",
        f"Generated prompt:\n {hcode(prompt)}",
        f"Revised prompt:\n {hcode(revised_prompt)}"
    ]
    await bot.send_message(chat_id=debug_chat_id, text="\n".join(messages))
    await bot.send_photo(chat_id=debug_chat_id, photo=photo)


class Action(str, Enum):
    ACTION_REGENERATE = "regenerate"


class CardGenerationCallback(CallbackData, prefix="my"):
    action: Action
    request_id: int


async def generate_image(client: AsyncOpenAI, prompt: str, user_id: str) -> Image:
    response = await client.images.generate(prompt=prompt, model="dall-e-3", response_format="b64_json", user=user_id)
    img = response.data[0]  # Api only returns one image
    return img


def generate_image_keyboad(locale: str, request_id: int) -> InlineKeyboardBuilder:
    button_label = i18n.t('regenerate', locale=locale)
    callback_data = CardGenerationCallback(action=Action.ACTION_REGENERATE, request_id=request_id).pack()
    buttons = [
        # [InlineKeyboardButton(text=button_label, callback_data=callback_data)],
        [InlineKeyboardButton(
            text=i18n.t("share_with_friend", locale=locale),
            switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(allow_user_chats=True,
                                                                        allow_group_chats=True,
                                                                        allow_channel_chats=True,
                                                                        query=str(request_id))
        )]
    ]

    return InlineKeyboardBuilder(markup=buttons)


async def finish(chat_id: int, request_id: int, bot: Bot, user: TelebotUsers, locale: str, client: AsyncOpenAI, debug_chat_id: int,
                 s3_uploader: S3Uploader, image_proxy: ImageProxy) -> None:
    answers = await CardRequestsAnswers.filter(request_id=request_id).all().values()
    data = {item['question'].value: item['answer'] for item in answers}
    prompt = generate_prompt(data=data, locale=locale)
    await CardRequests.filter(id=request_id).update(generated_prompt=prompt)

    try:
        async with ChatActionSender.upload_photo(bot=bot, chat_id=chat_id):
            image = await generate_image(prompt=prompt, user_id=str(user.id), client=client)
            image_bytes = base64.b64decode(image.b64_json)
            image_path = await s3_uploader.upload_image(image_bytes)
            await CardRequests.filter(id=request_id).update(revised_prompt=image.revised_prompt, result_image=image_path)

            keyboard = generate_image_keyboad(locale=locale, request_id=request_id)

            await TelebotUsers.filter(id=user.id).update(remaining_cards=F_SQL("remaining_cards") - 1)
            photo = URLInputFile(url=image_proxy.get_full_image(s3_uploader.get_full_s3_url(image_path)), filename="card.png")
            await bot.send_photo(chat_id=chat_id, photo=photo, reply_markup=keyboard.as_markup(), protect_content=True)

            await bot.send_message(chat_id=chat_id, text=i18n.t('commands.card', locale=locale))

            await debug_log(prompt_data=data, bot=bot, prompt=prompt, revised_prompt=image.revised_prompt,
                            photo=photo, user=user,
                            debug_chat_id=debug_chat_id)
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

    answers_dict = {item['answers__question']
                    : item['answers__answer'] for item in answers}

    prompt = i18n.t("card_form.depiction.depiction_prompt", locale=locale,
                    reason=answers_dict.get(CardRequestQuestions.REASON, ""),
                    relationship=answers_dict.get(CardRequestQuestions.RELATIONSHIP, ""),
                    description=answers_dict.get(CardRequestQuestions.DESCRIPTION, ""))
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


async def handle_no_more_cards(message: types.Message, user: types.User):
    locale = user.language_code

    kb = [[
        InlineKeyboardButton(
            text=i18n.t("invite_friend", locale=locale),
            switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(allow_user_chats=True,
                                                                        allow_group_chats=True,
                                                                        allow_channel_chats=True)
        )
    ]]
    await message.answer(
        i18n.t("no_cards_left", locale=locale),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


async def ensure_user_has_cards(message: types.Message, user: types.User = None) -> bool:
    telebot_user = await user_from_message(telegram_user=user)
    if telebot_user.remaining_cards <= 0:
        await handle_no_more_cards(message=message, user=user)
        return False
    return True


async def command_start(message: types.Message, state: FSMContext) -> None:
    locale = message.from_user.language_code
    user = await user_from_message(telegram_user=message.from_user)
    if await ensure_user_has_cards(message=message, user=message.from_user):
        request: CardRequests = await CardRequests.create(user=user, language_code=locale)
        await state.update_data(request_id=request.id)
        await state.set_state(CardForm.reason)
        answer_samples_keyboard = generate_answer_samples_keyboard(
            locale=locale, question=CardRequestQuestions.REASON, columns=1)
        await message.answer(i18n.t("card_form.reason.response", locale=locale), reply_markup=answer_samples_keyboard)


async def process_reason(message: types.Message, state: FSMContext) -> None:
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.REASON, answer=message.text, language_code=locale)
    await state.set_state(CardForm.description)
    answer_samples_keyboard = generate_answer_samples_keyboard(
        locale=locale, question=CardRequestQuestions.DESCRIPTION, columns=4)
    await message.answer(i18n.t(f"card_form.{CardRequestQuestions.DESCRIPTION.value}.response", locale=locale), reply_markup=answer_samples_keyboard)


async def process_description(message: types.Message, state: FSMContext, async_openai_client: AsyncOpenAI, bot: Bot) -> None:
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.DESCRIPTION, answer=message.text, language_code=locale)
    await state.set_state(CardForm.depiction)

    await message.answer(i18n.t("card_form.depiction.coming_up_with_ideas", locale=locale), reply_markup=ReplyKeyboardRemove())
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        depiction_ideas = await generate_depictions_samples_keyboard(locale=locale, request_id=request_id, client=async_openai_client)
        await message.answer(i18n.t(f"card_form.{CardRequestQuestions.DEPICTION.value}.response", locale=locale), reply_markup=depiction_ideas)


async def process_depiction(message: types.Message, state: FSMContext, async_openai_client: AsyncOpenAI, bot: Bot, settings: Settings,
                            s3_uploader: S3Uploader, image_proxy: ImageProxy) -> None:
    user = await user_from_message(telegram_user=message.from_user)
    locale = message.from_user.language_code
    request_id = (await state.get_data())['request_id']
    await CardRequestsAnswers.create(request_id=request_id, question=CardRequestQuestions.DEPICTION, answer=message.text, language_code=locale)
    await state.set_state(CardForm.style)

    await message.answer(i18n.t("card_form.wait.response", locale=locale), reply_markup=ReplyKeyboardRemove())
    await state.clear()
    await finish(chat_id=message.chat.id, request_id=request_id, bot=bot, user=user, locale=locale,
                 client=async_openai_client, debug_chat_id=settings.debug_chat_id, s3_uploader=s3_uploader, image_proxy=image_proxy)


async def regenerate(query: CallbackQuery, callback_data: CardGenerationCallback, bot: Bot,
                     async_openai_client: AsyncOpenAI, settings: Settings,
                     s3_uploader: S3Uploader, image_proxy: ImageProxy):
    if await ensure_user_has_cards(message=query.message, user=query.from_user):
        user = await user_from_message(telegram_user=query.from_user)
        locale = query.from_user.language_code
        await query.answer(text=i18n.t("card_form.wait.response", locale=locale))
        await finish(chat_id=query.message.chat.id, request_id=callback_data.request_id, bot=bot, user=user, locale=locale,
                     client=async_openai_client, debug_chat_id=settings.debug_chat_id, s3_uploader=s3_uploader, image_proxy=image_proxy)


async def inline_query(query: types.InlineQuery, bot: Bot,
                       s3_uploader: S3Uploader,
                       image_proxy: ImageProxy,
                       settings: Settings) -> None:
    user = await user_from_message(telegram_user=query.from_user)
    link = await create_start_link(bot, str(user.id))
    request_id = query.query
    results = []
    request_qs = CardRequests.filter(result_image__isnull=False, user=user).order_by("-created_at")
    if request_id:
        request_qs = request_qs.filter(id=request_id)
    requests = await request_qs.limit(8)
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=i18n.t("generate_your_own", locale=query.from_user.language_code), url=link)
        ]]
    )
    thumbnail_width = 256
    thumbnail_height = 256
    for request in requests:
        photo_url = image_proxy.get_full_image(s3_uploader.get_website_url(request.result_image))
        thumbnail_url = image_proxy.get_thumbnail(s3_uploader.get_website_url(request.result_image), width=thumbnail_width, height=thumbnail_height)

        logging.info(f"{photo_url=} {thumbnail_url=}")
        results.append(types.InlineQueryResultArticle(
            id=str(datetime.datetime.now()),
            title=i18n.t('shared_title', locale=query.from_user.language_code, name=query.from_user.full_name),
            description=i18n.t('shared_description', locale=query.from_user.language_code, name=query.from_user.full_name),
            thumbnail_width=thumbnail_width,
            thumbnail_height=thumbnail_height,
            thumbnail_url=thumbnail_url,
            input_message_content=types.InputTextMessageContent(
                message_text=i18n.t('share_message_content_markdown', locale=query.from_user.language_code,
                                    name=query.from_user.full_name, photo_url=photo_url),
                parse_mode="MarkdownV2",
            ),
            caption=i18n.t('shared_from', locale=query.from_user.language_code, name=query.from_user.full_name),
            reply_markup=reply_markup,
        ))

    await query.answer(results=results, cache_time=0)


async def chosen_inline_result_handler(chosen_inline_result: types.ChosenInlineResult):
    pass


async def edited_message_handler(edited_message: types.Message):
    pass


def register(dp: Dispatcher):
    form_router = Router()
    form_router.message(card_command)(command_start)
    form_router.message(CardForm.reason)(process_reason)
    form_router.message(CardForm.description)(process_description)
    form_router.message(CardForm.depiction)(process_depiction)
    form_router.callback_query(CardGenerationCallback.filter(F.action == Action.ACTION_REGENERATE))(regenerate)

    form_router.edited_message()(edited_message_handler)

    form_router.inline_query()(inline_query)
    form_router.chosen_inline_result()(chosen_inline_result_handler)

    dp.include_router(form_router)
