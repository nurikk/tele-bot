from unittest.mock import AsyncMock

import pytest

from src.db import CardRequests, CardRequestsAnswers, TelebotUsers, CardRequestQuestions
from src.main import init_i18n

from src.message_handlers.card import generate_descriptions_samples_keyboard, generate_depictions_samples_keyboard


def test_foo():
    pass


@pytest.mark.asyncio
async def test_generate_descriptions_samples_keyboard(in_memory_db):
    user = await TelebotUsers.create(id=1, telegram_id=123, username='test_user', full_name='Test User')
    for i in range(1, 10):
        request = await CardRequests.create(user=user)
        for language_code in ['en', 'ru']:
            for question in [CardRequestQuestions.DESCRIPTION, CardRequestQuestions.REASON]:
                await CardRequestsAnswers.create(request=request, question=question, answer=f'answer {i} {language_code} {question.value}',
                                                 language_code=language_code)
                await CardRequestsAnswers.create(request=request, question=question, answer=f'answer {i} {language_code} {question.value}',
                                                 language_code=language_code)

    await generate_descriptions_samples_keyboard(user, 'en')


@pytest.mark.asyncio
async def test_generate_depictions_samples_keyboard(in_memory_db):
    init_i18n()
    user = await TelebotUsers.create(id=1, telegram_id=123, username='test_user', full_name='Test User')
    for i in range(1, 10):
        request = await CardRequests.create(user=user)
        for language_code in ['en', 'ru']:
            for question in [CardRequestQuestions.DESCRIPTION, CardRequestQuestions.REASON, CardRequestQuestions.RELATIONSHIP]:
                await CardRequestsAnswers.create(request=request, question=question, answer=f'answer {i} {language_code} {question.value}',
                                                 language_code=language_code)

    await generate_depictions_samples_keyboard(locale='en', request_id=request.id)
