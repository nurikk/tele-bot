import pytest

from src import db


@pytest.mark.asyncio
async def test_get_near_holidays(db_mock):
    holidays = await db.get_near_holidays("ru", days=1)
    pass