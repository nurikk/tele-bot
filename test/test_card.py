from unittest.mock import AsyncMock, Mock, MagicMock, ANY, call

import pytest

from src.db import CardRequests, CardRequestsAnswers, TelebotUsers, CardRequestQuestions
from src.main import init_i18n

from src.message_handlers.card import generate_descriptions_samples_keyboard, generate_depictions_samples_keyboard, deliver_generated_samples_to_user, command_start, \
    generate_reason_samples_keyboard


def test_foo():
    pass


@pytest.mark.asyncio
async def test_generate_descriptions_samples_keyboard(db_mock):
    user = await TelebotUsers.filter(id=1).first()
    await generate_descriptions_samples_keyboard(user, 'en')


@pytest.mark.asyncio
async def test_generate_depictions_samples_keyboard(db_mock, mock_open_ai_client):
    init_i18n()
    user = await TelebotUsers.filter(id=1).first()
    request = await CardRequests.filter(user=user).first()

    await generate_depictions_samples_keyboard(locale='en', request_id=request.id, client=mock_open_ai_client)


@pytest.mark.asyncio
async def test_finish_decrease_cards(db_mock, mock_open_ai_client):
    # await db_mock
    user = await TelebotUsers.filter(id=1).first()
    assert user.remaining_cards == 5
    await deliver_generated_samples_to_user(chat_id=1, request_id=1, locale='en', user=user, bot=AsyncMock(), client=mock_open_ai_client, debug_chat_id=1, s3_uploader=AsyncMock())
    await deliver_generated_samples_to_user(chat_id=1, request_id=1, locale='en', user=user, bot=AsyncMock(), client=mock_open_ai_client, debug_chat_id=1, s3_uploader=AsyncMock())
    user = await TelebotUsers.filter(id=1).first()
    assert user.remaining_cards == 3


@pytest.mark.asyncio
async def test_command_start(db_mock, mock_open_ai_client):
    mock_telegram_user = Mock(id=1, language_code='en', full_name='', username='')
    mock_answer = AsyncMock()
    mock_message = MagicMock(from_user=mock_telegram_user, answer=mock_answer)
    mock_state = AsyncMock()
    await command_start(message=mock_message, state=mock_state)
    mock_answer.assert_awaited_with("card_form.reason.response", reply_markup=ANY)
    mock_answer.reset_mock()
    #
    await TelebotUsers.filter(id=1).update(remaining_cards=0)
    await command_start(message=mock_message, state=mock_state)
    mock_answer.assert_awaited_with("no_cards_left", reply_markup=ANY)


@pytest.mark.asyncio
async def test_generate_reason_samples_keyboard(db_mock):
    init_i18n()
    await generate_reason_samples_keyboard('ru')