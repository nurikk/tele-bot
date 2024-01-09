from enum import Enum

from aiogram.filters.callback_data import CallbackData


class Action(str, Enum):
    ACTION_REGENERATE = "regenerate"
    ACTION_BROADCAST = "broadcast"


class CardActionCallback(CallbackData, prefix="my"):
    action: Action
    request_id: int
