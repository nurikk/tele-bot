import re

from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand

start_command = CommandStart()
start_referral_command = CommandStart(deep_link=True)
card_bot_command = BotCommand(command="card", description="")
card_command = Command(card_bot_command)

stop_bot_command = BotCommand(command="stop", description="")
stop_command = Command(stop_bot_command)

img_command = Command(BotCommand(command="img", description="Generate a imagee"))

generate_broadcast = Command(re.compile(r"generate_broadcast_(en|ru)"))

calendar_bot_command = BotCommand(command="calendar", description="")
calendar = Command(calendar_bot_command)
