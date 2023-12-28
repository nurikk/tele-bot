from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand

start_command = CommandStart()
start_referral_command = CommandStart(deep_link=True)
card_command = Command(BotCommand(command="card", description="Generate a postcard"))
img_command = Command(BotCommand(command="img", description="Generate a imagee"))
