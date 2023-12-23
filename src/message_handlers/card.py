import json
import logging

import i18n
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, URLInputFile

from src.commands import card_command
from src.fsm.card import CardForm
from src.oai import client
from src.prompt_generator import generate_prompt


async def finish(message: types.Message, data: dict[str, any]) -> None:
    text = json.dumps(data, indent=4, ensure_ascii=False)
    logging.info(text)
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())

    prompt = generate_prompt(data=data, locale=message.from_user.language_code)
    await message.answer(
        prompt,
        reply_markup=ReplyKeyboardRemove(),
    )
    resp = await client.images.generate(prompt=prompt, model="dall-e-3")
    print(resp)
    for img in resp.data:
        await message.answer(text=img.revised_prompt, reply_markup=ReplyKeyboardRemove())
        image = URLInputFile(
            img.url,
            filename="card.png"
        )
        await message.reply_photo(
            image,
            reply_markup=ReplyKeyboardRemove(),
        )


def generate_message_handler(form_router, start_command, key: str, next_state, answer: str):
    @form_router.message(start_command)
    async def handler(message: types.Message, state: FSMContext) -> None:
        if key:
            logging.info(f"Updating data for {key=} {message.text=}")
            await state.update_data({key: message.text})
        if answer:
            await message.answer(i18n.t(answer, locale=message.from_user.language_code))
        if next_state:
            await state.set_state(next_state)
        else:
            await finish(message=message, data=await state.get_data())
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
