import abc
import asyncio
import logging
from typing import Literal

import replicate
from openai import AsyncOpenAI
from replicate import identifier
from replicate.exceptions import ModelError
from replicate.run import _make_output_iterator
from replicate.version import Versions
from tqdm.asyncio import tqdm


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

    async def async_run(self,
                        ref,
                        input,
                        **params,
                        ):
        version, owner, name, version_id = identifier._resolve(ref)

        if version or version_id:
            prediction = await self.client.predictions.async_create(
                version=(version or version_id), input=input or {}, **params
            )
        elif owner and name:
            prediction = await self.client.models.predictions.async_create(
                model=(owner, name), input=input or {}, **params
            )
        else:
            raise ValueError(
                f"Invalid argument: {ref}. Expected model, version, or reference in the format owner/name or owner/name:version"
            )

        if not version and (owner and name and version_id):
            version = Versions(self.client, model=(owner, name)).get(version_id)

        if version and (iterator := _make_output_iterator(version, prediction)):
            return iterator

        while prediction.status not in ["succeeded", "failed", "canceled"]:
            await asyncio.sleep(self.client.poll_interval)
            prediction.reload()

        if prediction.status == "failed":
            raise ModelError(prediction.error)

        return prediction.output

    async def generate(self, prompt: str, images_count: int = 1) -> list[str]:
        futures = [self.async_run(
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
        results = await tqdm.gather(*futures)
        return [r[0] for r in results]
