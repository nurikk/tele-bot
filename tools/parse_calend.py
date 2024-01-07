import asyncio
import json

from openai import AsyncOpenAI
from requests_html2 import HTMLSession
from tqdm import tqdm

from src.card_gen import ensure_english
from src.settings import Settings


async def parse_country(country: str, country_code: str):
    settings = Settings(_env_file='../.env')
    async_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    holidays = []
    url = f'https://www.calend.ru/holidays/{country}/'
    with HTMLSession() as session:
        response = session.get(url)
        elements = response.html.find(".datesList > ul > li")
        for el in tqdm(elements):
            date_num = el.find('.dataNum > a > .number').select(lambda e: e.text, first=True, default="")
            date_month = el.find('.dataNum > a > .desc > .title').select(lambda e: e.text, first=True, default="")
            titles = el.find('.caption > .title').select(lambda e: e.text, default=[])
            if country_code == 'en':
                titles = [await ensure_english(text=t, locale='ru', async_openai_client=async_openai_client) for t in titles]
            holidays.append({
                'date_num': date_num,
                'date_month': date_month,
                'titles': titles
            })

    with open(f'../src/holidays/{country_code}.json', 'w') as f:
        f.write(json.dumps(holidays))


if __name__ == "__main__":
    asyncio.run(parse_country('wholeworld', 'en'))

    # parse_country('russtate', 'ru')
