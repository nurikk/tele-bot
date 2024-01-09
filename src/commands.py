from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand

start_command = CommandStart()
start_referral_command = CommandStart(deep_link=True)
card_bot_command = BotCommand(command="card", description="Generate a postcard")
card_command = Command(card_bot_command)

stop_bot_command = BotCommand(command="stop", description="Stop the bot")
stop_command = Command(stop_bot_command)

img_command = Command(BotCommand(command="img", description="Generate a imagee"))


generate_broadcast = Command(BotCommand(command="generate_broadcast", description="Generate broadcast cards"))
broadcast = Command(BotCommand(command="broadcast", description="Broadcast card"))
