from aiogram.fsm.state import StatesGroup, State


class ImgForm(StatesGroup):
    prompt = State()
