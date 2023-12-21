from openai import OpenAI, AsyncOpenAI

from src.settings import settings

client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=settings.openai_api_key
)