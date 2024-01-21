import pytest
from openai import AsyncOpenAI

from src.main import init_i18n
from src.prompt_generator import generate_prompt


@pytest.mark.asyncio
async def test_generate_prompt(settings):
    init_i18n()
    async_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    # assert await generate_prompt(data={"reason": "New year",
    #                                    "relationship": "Friend",
    #                                    "description": "🦔",
    #                                    "depiction": "A hedgehog riding on a cheese wheel"}, locale="en", async_openai_client=async_openai_client) == ''

    assert (
        await generate_prompt(
            data={
                "reason": "Новый год",
                "relationship": "Друг",
                "description": "🦔",
                "depiction": "Еж катающийся на сырном колесе",
            },
            locale="ru",
            async_openai_client=async_openai_client,
        )
        == ""
    )
