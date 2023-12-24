import base64
import json
import logging

import i18n
from aiogram import types, Router, Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from aiogram.utils.markdown import hcode, hbold, hpre
from openai import BadRequestError

from src.commands import card_command
from src.db import user_from_message, User, CardRequest
from src.fsm.card import CardForm
from src.oai import client
from src.prompt_generator import generate_prompt
from src.settings import settings


async def debug_log(prompt_data: dict, bot: Bot, message: types.Message, prompt: str, revised_prompt: str, image: BufferedInputFile):
    await bot.send_message(chat_id=settings.debug_chat_id, text=f"New card for {hbold(message.from_user.full_name)} @{message.from_user.username}!")
    await bot.send_message(chat_id=settings.debug_chat_id, text=f"User response: \n {hpre(json.dumps(prompt_data, indent=4))}")
    await bot.send_message(chat_id=settings.debug_chat_id, text=f"Generated prompt:\n {hcode(prompt)}")
    await bot.send_message(chat_id=settings.debug_chat_id, text=f"Revised prompt:\n {hcode(revised_prompt)}")
    await bot.send_photo(chat_id=settings.debug_chat_id, photo=image)


async def finish(message: types.Message, data: dict[str, any], bot: Bot, user: User) -> None:
    prompt = generate_prompt(data=data, locale=message.from_user.language_code)
    request = await CardRequest.objects.create(user=user,
                                               request=data,
                                               generated_prompt=prompt,
                                               language_code=message.from_user.language_code)
    try:
        img = (await client.images.generate(prompt=prompt, model="dall-e-3", response_format="b64_json"))[0]  # Api only returns one image

        image = BufferedInputFile(file=base64.b64decode(img.b64_json), filename="card.png")  # TODO: save images to s3
        await bot.send_photo(chat_id=message.chat.id, photo=image)
        await bot.send_message(chat_id=message.chat.id, text=i18n.t('commands.card', locale=message.from_user.language_code))

        await request.update(revised_prompt=img.revised_prompt)
        await debug_log(prompt_data=data, bot=bot, message=message, prompt=prompt, revised_prompt=img.revised_prompt, image=image)
    except BadRequestError as e:
        await message.reply(text=e.body['message'])


def generate_message_handler(form_router: Router, start_command, key: str, next_state, answer: str):
    @form_router.message(start_command)
    async def handler(message: types.Message, state: FSMContext, bot: Bot) -> None:
        user = await user_from_message(message=message)
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
            await finish(message=message, data=data, bot=bot, user=user)


def register(dp: Dispatcher):
    form_router = Router()
    commands = [
        (card_command, CardForm.reason, None, "card_form.reason"),
        (CardForm.reason, CardForm.relationship, "reason", "card_form.relationship"),
        (CardForm.relationship, CardForm.description, "relationship", "card_form.description"),
        (CardForm.description, CardForm.depiction, "description", "card_form.depiction"),
        (CardForm.depiction, CardForm.style, "depiction", "card_form.style"),
        (CardForm.style, None, "style", "card_form.wait")
    ]

    for start_command, next_state, key, question in commands:
        generate_message_handler(form_router, start_command, key, next_state, question)

    dp.include_router(form_router)
