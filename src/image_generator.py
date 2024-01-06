import abc

from openai import AsyncOpenAI
import replicate


class ImageGenerator(abc.ABC):
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError()


class OpenAIGenerator(ImageGenerator):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, prompt: str) -> str:
        response = await self.client.images.generate(prompt=prompt, model="dall-e-3")
        return response.data[0].url  # Api only returns one image


class ReplicateGenerator(ImageGenerator):
    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)

    async def generate(self, prompt: str) -> str:
        output = await self.client.async_run(
            "playgroundai/playground-v2-1024px-aesthetic:42fe626e41cc811eaf02c94b892774839268ce1994ea778eba97103fe1ef51b8",
            input={
                "width": 1024,
                "height": 1024,
                "prompt": prompt,
                "scheduler": "K_EULER_ANCESTRAL",
                "guidance_scale": 3,
                "apply_watermark": False,
                "negative_prompt": "",
                "num_inference_steps": 50
            }
        )
        return output[0]
