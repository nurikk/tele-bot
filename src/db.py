import logging
from enum import Enum

from aiogram import types

from src.settings import settings

from tortoise.models import Model
from tortoise import fields, Tortoise


async def user_from_message(telegram_user: types.User):
    user_props = {
        "full_name": telegram_user.full_name,
        "username": telegram_user.username
    }
    (user, is_new) = await TelebotUsers.update_or_create(telegram_id=telegram_user.id, defaults=user_props)
    logging.info(f"User {user.full_name} {'created' if is_new else 'updated'}")
    return user


class TelebotUsers(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    last_seen = fields.DatetimeField(auto_now=True)
    telegram_id = fields.BigIntField(unique=True, index=True)
    full_name = fields.TextField(null=True)
    username = fields.TextField()


class CardRequestQuestions(str, Enum):
    REASON = "reason"
    RELATIONSHIP = "relationship"
    DESCRIPTION = "description"
    DEPICTION = "depiction"
    STYLE = "style"


class CardRequests(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    user = fields.ForeignKeyField("models.TelebotUsers", related_name="requests", index=True)
    generated_prompt = fields.TextField(null=True)
    revised_prompt = fields.TextField(null=True)


class CardRequestsAnswers(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    request = fields.ForeignKeyField("models.CardRequests", related_name="answers", index=True)
    language_code = fields.TextField()
    question = fields.CharEnumField(CardRequestQuestions, index=True)
    answer = fields.TextField()


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
