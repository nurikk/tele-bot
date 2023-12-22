import json
import logging

from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, URLInputFile

from src.commands import card_command
from src.fsm.card import CardForm
from src.oai import client
from src.prompt_generator import generate_prompt


def register(dp):
    form_router = Router()

    @form_router.message(card_command)
    async def handler(message: types.Message, state: FSMContext) -> None:
        await state.set_state(CardForm.reason)
        await message.answer(
            "What's the reason of postcard? (merry christmas, birthday, etc)",
            reply_markup=ReplyKeyboardRemove(),
        )

    @form_router.message(CardForm.reason)
    async def process_reason(message: types.Message, state: FSMContext) -> None:
        await state.update_data(reason=message.text)
        await state.set_state(CardForm.relationship)
        await message.answer(
            f"What is your relationship with the person being congratulated?",
            reply_markup=ReplyKeyboardRemove(),
        )

    @form_router.message(CardForm.relationship)
    async def process_relationship(message: types.Message, state: FSMContext) -> None:
        await state.update_data(relationship=message.text)
        await state.set_state(CardForm.description)
        await message.answer(
            f"Describe the person being congratulated.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @form_router.message(CardForm.description)
    async def process_relationship(message: types.Message, state: FSMContext) -> None:
        await state.update_data(description=message.text)
        await state.set_state(CardForm.depiction)
        await message.answer(
            f"What would you like to depict on a postcard?",
            reply_markup=ReplyKeyboardRemove(),
        )

    @form_router.message(CardForm.depiction)
    async def process_depiction(message: types.Message, state: FSMContext) -> None:
        await state.update_data(depiction=message.text)
        await state.set_state(CardForm.style)
        await message.answer(
            f"Choose the postcard style.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @form_router.message(CardForm.style)
    async def process_style(message: types.Message, state: FSMContext) -> None:
        data = await state.update_data(style=message.text)

        await state.clear()

        await show_summary(message=message, data=data)

    async def show_summary(message: types.Message, data: dict[str, any]) -> None:
        text = json.dumps(data, indent=4, ensure_ascii=False)
        logging.info(text)
        await message.answer(text=text, reply_markup=ReplyKeyboardRemove())
        await message.answer(
            "Please wait for the image to be generated",
            reply_markup=ReplyKeyboardRemove(),
        )
        prompt = generate_prompt(data=data, user=message.from_user)
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


    dp.include_router(form_router)
