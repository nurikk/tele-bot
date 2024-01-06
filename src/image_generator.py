import abc

from openai import AsyncOpenAI


class ImageGenerator(abc.ABC):
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError()


class OpenAIGenerator(ImageGenerator):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, prompt: str) -> str:
        response = await self.client.images.generate(prompt=prompt, model="dall-e-3")
        return response.data[0].url  # Api only returns one image
