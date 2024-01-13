import json
import random

import i18n
from openai import AsyncOpenAI

from src import db


def generate_prompt(data: dict[str, str], locale: str) -> str:
    style_samples = i18n.t("style_samples", locale=locale).split(",")
    style = random.choice(style_samples)
    return i18n.t("prompt", locale=locale, style=style, **data)


async def get_depiction_ideas(request_id: int, locale: str, client: AsyncOpenAI) -> list[str]:
    answers = await db.CardRequests.filter(id=request_id,
                                           answers__language_code=locale,
                                           answers__question__in=[db.CardRequestQuestions.DESCRIPTION,
                                                                  db.CardRequestQuestions.REASON,
                                                                  db.CardRequestQuestions.RELATIONSHIP]
                                           ).values('answers__question', 'answers__answer')

    answers_dict = {item['answers__question']: item['answers__answer'] for item in answers}


    prompt = i18n.t("card_form.depiction.depiction_prompt", locale=locale,
                    reason=answers_dict.get(db.CardRequestQuestions.REASON, ""),
                    relationship=answers_dict.get(db.CardRequestQuestions.RELATIONSHIP, ""),
                    description=answers_dict.get(db.CardRequestQuestions.DESCRIPTION, ""))
    stream = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system",
             "content": "You are a AI designed for postcard depiction ideas generation. You have to give five short funny ideas for a depiction. Don't add any details, just two short ideas. Don't add numerals or headings. Format output as a valid json array. Produce ideas in the same language as the prompt."},
            {"role": "user", "content": prompt}
        ]
    )
    samples = []
    try:
        samples = json.loads(stream.choices[0].message.content)
    except json.decoder.JSONDecodeError:
        pass
    return samples


async def get_greeting_text(async_openai_client: AsyncOpenAI, reason: str):
    greeting_text = await async_openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": ",".join([
                "You are a helpful assistant",
                "User will provide a holiday name and you have to generate a short greeting for a postcard"
                "Don't add much details, just two short sentences separated by a semicolon",
                "Produce output in the same language as the prompt"]
            )},
            {"role": "user", "content": reason},
        ]
    )
    return greeting_text.choices[0].message.content
