import abc
import asyncio
import logging
from typing import Literal

from openai import AsyncOpenAI
import replicate


class ImageGenerator(abc.ABC):
    async def generate(self, prompt: str, images_count: int = 1) -> list[str]:
        raise NotImplementedError()


class OpenAIGenerator(ImageGenerator):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, prompt: str, images_count: Literal[1] = 1) -> list[str]:
        response = await self.client.images.generate(prompt=prompt, model="dall-e-3")
        return [r.url for r in response.data]


class ReplicateGenerator(ImageGenerator):
    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)
        self.api_token = api_token

    async def generate(self, prompt: str, images_count: int = 1) -> list[str]:
        # return await self.client.async_run(
        #     "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        #     input={
        #         "width": 768,
        #         "height": 768,
        #         "prompt": prompt,
        #         "refine": "expert_ensemble_refiner",
        #         "scheduler": "K_EULER",
        #         "lora_scale": 0.6,
        #         "num_outputs": 4,
        #         "guidance_scale": 7.5,
        #         "apply_watermark": False,
        #         "high_noise_frac": 0.8,
        #         "negative_prompt": "",
        #         "prompt_strength": 0.8,
        #         "num_inference_steps": 25
        #     }
        # )
        futures = [self.client.async_run(
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
        ) for _ in range(images_count)]
        logging.info(f"Starting {len(futures)} image generation tasks")
        results = await asyncio.gather(*futures)
        return [r[0] for r in results]
