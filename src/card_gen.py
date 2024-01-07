from openai import AsyncOpenAI

from src import db
from src.image_generator import ImageGenerator
from tortoise.expressions import F
from src.prompt_generator import generate_prompt
from src.s3 import S3Uploader


async def ensure_english(text: str, locale: str, async_openai_client: AsyncOpenAI) -> str:
    if locale != 'en':
        response = await async_openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You will be provided with a sentence in Russian, and your task is to translate it into English."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.7,
            max_tokens=int(len(text) * 1.5),
            top_p=1
        )
        return response.choices[0].message.content
    return text


async def render_card(request_id: int, user: db.TelebotUsers, locale: str, image_generator: ImageGenerator,
                      s3_uploader: S3Uploader, async_openai_client: AsyncOpenAI, images_count: int = 2):
    answers = await db.CardRequestsAnswers.filter(request_id=request_id).all().values()
    data = {item['question'].value: item['answer'] for item in answers}
    prompt = await ensure_english(text=generate_prompt(data=data, locale=locale), locale=locale, async_openai_client=async_openai_client)
    await db.CardRequests.filter(id=request_id).update(generated_prompt=prompt)
    generated_images = await image_generator.generate(prompt=prompt, images_count=images_count)
    image_paths = []
    for image_url in generated_images:
        image_path = await s3_uploader.upload_image_from_url(image_url=image_url)
        image_paths.append(await db.CardResult.create(request_id=request_id, result_image=image_path))
    await db.TelebotUsers.filter(id=user.id).update(remaining_cards=F("remaining_cards") - 1)


async def generate_cards(image_generator: ImageGenerator, s3_uploader: S3Uploader,
                         async_openai_client: AsyncOpenAI, cards_per_holiday: int = 5):
    system_user = (await db.TelebotUsers.get_or_create(telegram_id=0,
                                                       defaults={"full_name": "CARD GENERATOR",
                                                                 "username": "__system__bot__",
                                                                 "user_type": db.UserType.System}))[0]
    for locale in ["ru"]:
        near_holidays = await db.get_near_holidays(locale, days=7)
        for holiday in near_holidays:
            for i in range(cards_per_holiday):
                card_request = await db.CardRequests.create(user=system_user)
                await db.CardRequestsAnswers.create(request_id=card_request.id,
                                                    question=db.CardRequestQuestions.REASON,
                                                    answer=holiday.title,
                                                    language_code=locale)
                await render_card(request_id=card_request.id, user=system_user,
                                  locale=locale, image_generator=image_generator, s3_uploader=s3_uploader,
                                  async_openai_client=async_openai_client)
