import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from dotenv import find_dotenv, load_dotenv
from tortoise import Tortoise
from tortoise.contrib.test import getDBConfig, _init_db

from src.db import CardRequestQuestions, CardRequests, CardRequestsAnswers, TelebotUsers, Holidays


# @pytest.fixture(scope="session")
# def event_loop():
#     try:
#         loop = asyncio.get_running_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#     yield loop
#     loop.close()


@pytest.fixture
def in_memory_db(request, event_loop):
    config = getDBConfig(app_label="models", modules=["src.db"])
    event_loop.run_until_complete(_init_db(config))
    request.addfinalizer(lambda: event_loop.run_until_complete(Tortoise._drop_databases()))


current_date = datetime(2021, 1, 1)


@pytest.fixture
def db_mock(in_memory_db, event_loop):
    async def code():
        all_questions = [CardRequestQuestions.DESCRIPTION,
                         CardRequestQuestions.REASON,
                         CardRequestQuestions.RELATIONSHIP]

        for i in range(1, 10):
            user = await TelebotUsers.create(id=i, telegram_id=i, username=f'test_user {i}', full_name=f'Test User {i}')
            for x in range(1, 10):
                request = await CardRequests.create(user=user)
                for language_code in ['en', 'ru']:
                    await Holidays.create(country_code=language_code, date=current_date + timedelta(days=x), title=f'holiday {i} {x} {language_code}',
                                          description=f'description {i} {x} {language_code}',
                                          url=f'url {i} {x} {language_code}')
                    for question in all_questions:
                        await CardRequestsAnswers.create(request=request,
                                                         question=question,
                                                         answer=f'answer {i} {language_code} {question.value}',
                                                         language_code=language_code)

        await TelebotUsers.create(telegram_id=309511727, username='anonymass', full_name=f'Anonymass')

    event_loop.run_until_complete(code())


@pytest.fixture
def mock_open_ai_client():
    mock_async_openai_client = AsyncMock()
    mock_message = Mock(content='{}')
    mock_choice = Mock(message=mock_message)
    mock_image_response = Mock(b64_json='', revised_prompt='')

    mock_async_openai_client.images.generate.return_value = Mock(data=[mock_image_response])
    mock_async_openai_client.chat.completions.create.return_value = Mock(choices=[mock_choice])
    yield mock_async_openai_client


@pytest.fixture
def settings():
    from src.settings import Settings
    return Settings(_env_file=find_dotenv('.env', raise_error_if_not_found=True, usecwd=True))
