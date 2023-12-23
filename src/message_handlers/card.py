import json
import logging

import i18n
from aiogram import types, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, URLInputFile
from aiogram.utils.markdown import hcode, hbold

from src.commands import card_command
from src.fsm.card import CardForm
from src.oai import client
from src.prompt_generator import generate_prompt


async def finish(message: types.Message, data: dict[str, any], bot: Bot) -> None:
    text = json.dumps(data, indent=4, ensure_ascii=False)
    logging.info(text)
    prompt = generate_prompt(data=data, locale=message.from_user.language_code)
    resp = await client.images.generate(prompt=prompt, model="dall-e-3")
    for img in resp.data:
        image = URLInputFile(img.url, filename="card.png")
        await bot.send_photo(chat_id=message.chat.id, photo=image)
        await bot.send_message(chat_id=message.chat.id, text=i18n.t('commands.card', locale=message.from_user.language_code))

        await bot.send_message(chat_id=-4028365371, text=f"New card for {hbold(message.from_user.full_name)} @{message.from_user.username}!")
        await bot.send_message(chat_id=-4028365371, text=hcode(prompt))
        await bot.send_message(chat_id=-4028365371, text=hcode(img.revised_prompt))
        await bot.send_photo(chat_id=-4028365371, photo=image)


def generate_message_handler(form_router: Router, start_command, key: str, next_state, answer: str):
    @form_router.message(start_command)
    async def handler(message: types.Message, state: FSMContext, bot: Bot) -> None:
        if key:
            logging.info(f"Updating data for {key=} {message.text=}")
            await state.update_data({key: message.text})
        if answer:
            await message.answer(i18n.t(answer, locale=message.from_user.language_code))
        if next_state:
            await state.set_state(next_state)
        else:
            await finish(message=message, data=await state.get_data(), bot=bot)
            await state.clear()


def register(dp):
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
