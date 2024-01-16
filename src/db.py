import datetime
import json
import logging
import os
from enum import Enum

import i18n
from aiogram import types, Bot
from tortoise import fields, Tortoise, connections
from tortoise.expressions import F as F_SQL
from tortoise.models import Model


async def handle_referral(user_id: int, bot: Bot = None, cards_per_user: int = 5):
    logging.info(f"Adding {cards_per_user} cards to user {user_id}")
    referee = await TelebotUsers.filter(id=user_id).first()
    await TelebotUsers.filter(id=user_id).update(remaining_cards=F_SQL("remaining_cards") + cards_per_user)
    if referee.remaining_cards <= 0 and bot:
        await bot.send_message(chat_id=referee.telegram_id, text=i18n.t("referral_bonus_granted", locale="en"))


async def user_from_message(telegram_user: types.User, referred_by: int = None, bot: Bot = None, cards_per_user: int = 5):
    user_props = {
        "full_name": telegram_user.full_name,
        "username": telegram_user.username,
        "remaining_cards": cards_per_user,
        "referred_by": await TelebotUsers.filter(id=referred_by).first() if referred_by else None
    }
    (user, is_new) = await TelebotUsers.get_or_create(telegram_id=telegram_user.id, defaults=user_props)
    if is_new and referred_by:
        logging.info(f"Registered new referral user {user.full_name}(@{user.username}) new user, referred by {referred_by}")
        await handle_referral(user_id=referred_by, bot=bot)
    if not is_new:
        await TelebotUsers.filter(id=user.id).update(last_seen=get_today())
    logging.info(f"User {user.full_name} {'created' if is_new else 'updated'}")
    return user


class TelebotUsers(Model):
    id: int = fields.IntField(pk=True)
    referred_by = fields.ForeignKeyField("models.TelebotUsers", related_name="referrals", null=True, index=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    last_seen: datetime.datetime = fields.DatetimeField(auto_now=True)
    telegram_id: int = fields.BigIntField(unique=True, index=True)
    full_name: str = fields.TextField(null=True)
    username: str = fields.TextField(null=True)
    remaining_cards: int = fields.IntField(default=5)
    is_stopped: bool = fields.BooleanField(default=False)
    is_admin: bool = fields.BooleanField(default=False)


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
    greeting_text: str = fields.TextField(null=True)
    shares_count: int = fields.IntField(default=0)
    is_public: bool = fields.BooleanField(default=False)


class CardResult(Model):
    id: int = fields.IntField(pk=True)
    request = fields.ForeignKeyField("models.CardRequests", related_name="results", index=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    result_image: str = fields.TextField(null=True)


class CardShareEvent(Model):
    id: int = fields.IntField(pk=True)
    request = fields.ForeignKeyField("models.CardRequests", related_name="shares", index=True)
    user = fields.ForeignKeyField("models.TelebotUsers", related_name="shares", index=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)


class CardRequestsAnswers(Model):
    id: int = fields.IntField(pk=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    request = fields.ForeignKeyField("models.CardRequests", related_name="answers", index=True)
    language_code: str = fields.TextField()
    question = fields.CharEnumField(CardRequestQuestions, index=True)
    answer: str = fields.TextField()


class Holidays(Model):
    id: int = fields.IntField(pk=True)
    created_at: datetime.datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime.datetime = fields.DatetimeField(auto_now=True)

    country_code: str = fields.TextField()
    date: datetime.date = fields.DateField()
    title: str = fields.TextField()
    description: str = fields.TextField()
    url: str = fields.TextField()

    def full_title(self):
        return f"{self.title} ({self.date.day} {i18n.t(f'month_names.month_{self.date.month}', locale=self.country_code)})"


def get_today():
    return datetime.datetime.utcnow()


async def get_near_holidays(country_code: str, days: int = 7) -> list[Holidays]:
    current_date = get_today()
    holidays = await Holidays.filter(country_code=country_code,
                                     date__gte=current_date.date(),
                                     date__lt=current_date.date() + datetime.timedelta(days=days),
                                     ).order_by("date").all()
    return holidays


TORTOISE_ORM = {
    "connections": {"default": os.environ.get('DB_URL', 'postgres://localhost:5432/telebot2')},
    "apps": {
        "models": {
            "models": ["src.db", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def start(db_url: str):
    await Tortoise.init(config={
        "connections": {"default": db_url},
        "apps": {
            "models": {
                "models": ["src.db", "aerich.models"],
                "default_connection": "default",
            },
        },
    }, use_tz=True)


def normalise_month_name(month_name: str) -> int:
    russian_months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return russian_months.index(month_name) + 1


async def get_user_ids_for_locale(locale: str) -> list[int]:
    conn = connections.get("default")
    SQL = """
    with _data as (
        select
        u.id,
        case
            WHEN a.language_code != 'ru' then 'en'
            else a.language_code
        end as language_code
        from
            telebotusers u
            left join cardrequests r on u.id = r.user_id
            left join cardrequestsanswers a on r.id = a.request_id
            where u.telegram_id != 0
        group by
            1,
            2
        )
    select id from _data where language_code = $1
    """
    val = await conn.execute_query_dict(SQL, [locale])
    return [v['id'] for v in val]


async def load_holidays():
    for country in i18n.config.settings['available_locales']:
        loaded_holidays = await Holidays.filter(country_code=country).count()
        if loaded_holidays == 0:
            logging.info(f"Loading holidays for {country}")
            file_abs_path = os.path.join(os.path.dirname(__file__), f"holidays/{country}.json")
            with open(file_abs_path) as f:
                holidays = json.load(f)
                for day in holidays:
                    for holiday_description in day['holidays']:
                        await Holidays.create(country_code=country,
                                              date=datetime.datetime.strptime(day['date'], "%Y-%m-%d").date(),
                                              title=holiday_description['title'],
                                              description=holiday_description['description'],
                                              url=holiday_description['url'])
