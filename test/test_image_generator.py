import pytest

from src.image_generator import ReplicateGenerator


@pytest.mark.asyncio
async def test_gen_image(settings):
    generator = ReplicateGenerator(api_token=settings.replicate_api_token)
    res = await generator.generate("Kittens playing with yarn")
    pass
