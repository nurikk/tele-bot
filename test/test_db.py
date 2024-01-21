from unittest.mock import patch

import pytest

from conftest import current_date
from src import db


@pytest.mark.asyncio
@patch("src.db.get_today", return_value=current_date)
async def test_get_near_holidays(mock_get_today, db_mock):
    holidays = await db.get_near_holidays("ru", days=3)
    assert len(holidays) == 1
