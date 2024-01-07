import pytest

from src import card_gen


@pytest.mark.asyncio
async def test_generate_cards(db_mock):
    await card_gen.generate_cards()
