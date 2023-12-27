import asyncio
import pytest
from tortoise import Tortoise
from tortoise.contrib.test import getDBConfig, _init_db


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def in_memory_db(request, event_loop):
    config = getDBConfig(app_label="models", modules=["src.db"])
    event_loop.run_until_complete(_init_db(config))
    request.addfinalizer(lambda: event_loop.run_until_complete(Tortoise._drop_databases()))
