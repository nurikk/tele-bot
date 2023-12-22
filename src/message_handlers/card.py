import json
import logging

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

    prompt = generate_prompt(data=data)
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
            await message.answer(answer)
        if next_state:
            await state.set_state(next_state)
        else:
            await finish(message=message, data=await state.get_data())
            await state.clear()


def register(dp):
    form_router = Router()
    commands = [
        (card_command, CardForm.reason, None, "What's the reason of postcard? (Ex: merry christmas, birthday, etc)"),
        (CardForm.reason, CardForm.relationship, "reason", "What is your relationship with the person being congratulated? (Ex: fried, daughter, wife)"),
        (CardForm.relationship, CardForm.description, "relationship", "Describe the person being congratulated. (Ex: my friend is 40 years old and loves to travel)"),
        (CardForm.description, CardForm.depiction, "description", "What would you like to depict on a postcard? (Ex: him riding a dragon and flying over the moon)"),
        (CardForm.depiction, CardForm.style, "depiction", "Choose the postcard style. (Ex: cartoon, watercolor, andy warhol)"),
        (CardForm.style, None, "style", "Please wait for the image to be generated."),
    ]

    for start_command, next_state, key, question in commands:
        generate_message_handler(form_router, start_command, key, next_state, question)

    dp.include_router(form_router)
