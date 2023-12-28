from unittest.mock import AsyncMock, Mock

import pytest

from src.db import CardRequests, CardRequestsAnswers, TelebotUsers, CardRequestQuestions
from src.main import init_i18n

from src.message_handlers.card import generate_descriptions_samples_keyboard, generate_depictions_samples_keyboard, finish


def test_foo():
    pass


@pytest.mark.asyncio
async def test_generate_descriptions_samples_keyboard(db_mock):
    await db_mock
    user = await TelebotUsers.filter(id=1).first()
    await generate_descriptions_samples_keyboard(user, 'en')


@pytest.mark.asyncio
async def test_generate_depictions_samples_keyboard(db_mock, mock_open_ai_client):
    await db_mock
    init_i18n()
    user = await TelebotUsers.filter(id=1).first()
    request = await CardRequests.filter(user=user).first()

    await generate_depictions_samples_keyboard(locale='en', request_id=request.id, client=mock_open_ai_client)


@pytest.mark.asyncio
async def test_finish_decrease_cards(db_mock, mock_open_ai_client):
    await db_mock
    user = await TelebotUsers.filter(id=1).first()
    assert user.remaining_cards == 5
    await finish(chat_id=1, request_id=1, locale='en', user=user, bot=AsyncMock(), client=mock_open_ai_client)
    await finish(chat_id=1, request_id=1, locale='en', user=user, bot=AsyncMock(), client=mock_open_ai_client)
    user = await TelebotUsers.filter(id=1).first()
    assert user.remaining_cards == 3
