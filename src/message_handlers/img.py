import json

from aiogram import types
from aiogram.types import ReplyKeyboardRemove

from src.commands import card_command, img_command

from src.oai import client


def register(dp):

    @dp.message(img_command)
    async def handler(message: types.Message) -> None:
        await message.answer(
            "Please wait for the image to be generated",
            reply_markup=ReplyKeyboardRemove(),
        )
        resp = await client.images.generate(prompt="cute cats playing with yarn", model="dall-e-3")
        await message.answer(
            resp.data[0].url,
            reply_markup=ReplyKeyboardRemove(),
        )

