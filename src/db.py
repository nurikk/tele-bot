import datetime
import logging

import databases
import orm
from aiogram import types

from src.settings import settings

database = databases.Database(settings.db_url)
models = orm.ModelRegistry(database=database)


async def user_from_message(user: types.User):
    (user, is_new) = await User.objects.update_or_create(telegram_id=user.id, defaults={
        "telegram_id": user.id,
        "full_name": user.full_name,
        "username": user.username
    })
    logging.info(f"User {user} is new: {is_new}")
    return user


class User(orm.Model):
    tablename = "users"
    registry = models
    fields = {
        "id": orm.Integer(primary_key=True),
        "created_at": orm.DateTime(auto_now_add=True),
        "last_seen": orm.DateTime(auto_now=True),
        "telegram_id": orm.BigInteger(unique=True, index=True),
        "full_name": orm.String(max_length=1000),
        "username": orm.String(max_length=1000),
    }


class CardRequest(orm.Model):
    tablename = "card_requests"
    registry = models
    fields = {
        "id": orm.Integer(primary_key=True),
        "created_at": orm.DateTime(auto_now_add=True),
        "user": orm.ForeignKey(User),
        "request": orm.JSON(),
        "language_code": orm.String(max_length=5),
        "generated_prompt": orm.String(max_length=100000),
        "revised_prompt": orm.String(max_length=100000, allow_null=True),
    }


metadata = models.metadata


async def start():
    await database.connect()
