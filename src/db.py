import datetime
import logging
from enum import Enum

from aiogram import types

from src.settings import settings

from tortoise.models import Model
from tortoise import fields, Tortoise
from tortoise.expressions import F as F_SQL


async def handle_referral(user_id: int):
    logging.info(f"Adding {settings.cards_per_user} cards to user {user_id}")
    await TelebotUsers.filter(id=user_id).update(remaining_cards=F_SQL("remaining_cards") + settings.cards_per_user)


async def user_from_message(telegram_user: types.User, referred_by: int = None):
    user_props = {
        "full_name": telegram_user.full_name,
        "username": telegram_user.username,
        "remaining_cards": settings.cards_per_user,
        "referred_by": await TelebotUsers.filter(id=referred_by).first() if referred_by else None
    }
    (user, is_new) = await TelebotUsers.get_or_create(telegram_id=telegram_user.id, defaults=user_props)
    if is_new and referred_by:
        logging.info(f"Registered new referral user {user.full_name}(@{user.username}) new user, referred by {referred_by}")
        await handle_referral(user_id=referred_by)
    logging.info(f"User {user.full_name} {'created' if is_new else 'updated'}")
    return user


class TelebotUsers(Model):
    id: int = fields.IntField(pk=True)
    referred_by = fields.ForeignKeyField("models.TelebotUsers", related_name="referrals", null=True, index=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    last_seen: datetime.datetime = fields.DatetimeField(auto_now=True)
    telegram_id: int = fields.BigIntField(unique=True, index=True)
    full_name: str = fields.TextField(null=True)
    username: str = fields.TextField()
    remaining_cards: int = fields.IntField(default=settings.cards_per_user)


class CardRequestQuestions(str, Enum):
    REASON = "reason"
    RELATIONSHIP = "relationship"
    DESCRIPTION = "description"
    DEPICTION = "depiction"
    STYLE = "style"


class CardRequests(Model):
    id: int = fields.IntField(pk=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    user = fields.ForeignKeyField("models.TelebotUsers", related_name="requests", index=True)
    generated_prompt: str = fields.TextField(null=True)
    revised_prompt: str = fields.TextField(null=True)


class CardRequestsAnswers(Model):
    id: int = fields.IntField(pk=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    request = fields.ForeignKeyField("models.CardRequests", related_name="answers", index=True)
    language_code: str = fields.TextField()
    question = fields.CharEnumField(CardRequestQuestions, index=True)
    answer: str = fields.TextField()


TORTOISE_ORM = {
    "connections": {"default": settings.db_url},
    "apps": {
        "models": {
            "models": ["src.db", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def start():
    await Tortoise.init(config=TORTOISE_ORM, use_tz=True)
