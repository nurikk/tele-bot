from aiogram import types, Router, Dispatcher, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import  URLInputFile
from aiogram.utils.markdown import hcode

from src.commands import img_command
from src.fsm.img import ImgForm

from src.oai import client


def register(dp: Dispatcher):
    form_router = Router()

    @form_router.message(img_command)
    async def command_start(message: types.Message, state: FSMContext) -> None:
        await state.set_state(ImgForm.prompt)
        await message.answer("Hi there! What's your prompt?")

    @form_router.message(ImgForm.prompt)
    async def process_dont_like_write_bots(message: types.Message, state: FSMContext, bot: Bot) -> None:
        await message.answer("Hold my beer!")
        await state.clear()
        prompt = message.text
        resp = await client.images.generate(prompt=prompt, model="dall-e-3")
        for img in resp.data:
            image = URLInputFile(img.url, filename="img.png")

            await bot.send_message(chat_id=message.chat.id, text=hcode(img.revised_prompt))
            await bot.send_photo(chat_id=message.chat.id, photo=image)

    dp.include_router(form_router)
