import asyncio
import json
import icalendar

from openai import AsyncOpenAI
from tqdm import tqdm

from src.prompt_generator import ensure_english
from src.settings import Settings
import requests


async def parse_country(country: str, country_code: str, year: int = 2024):
    settings = Settings(_env_file="../.env")
    async_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    holidays = []
    url = f"https://www.calend.ru/ical/ical-{country}.ics?v=yy{year}&b=1"
    ical_data = requests.get(url).text
    calendar = icalendar.Calendar.from_ical(ical_data)
    for event in tqdm(calendar.walk("VEVENT")):
        title = event.get("summary")
        description = event.get("description")
        url = event.get("url")
        if country_code == "en":
            title = await ensure_english(
                text=title, locale="ru", async_openai_client=async_openai_client
            )
            description = await ensure_english(
                text=description, locale="ru", async_openai_client=async_openai_client
            )
        holidays.append(
            {
                "date": event.get("dtstart").dt.strftime("%Y-%m-%d"),
                "holidays": [{"title": title, "description": description, "url": url}],
            }
        )

    with open(f"../src/holidays/{country_code}.json", "w") as f:
        f.write(json.dumps(holidays))


if __name__ == "__main__":
    asyncio.run(parse_country("wholeworld", "en"))
    # asyncio.run(parse_country('russtate', 'ru'))
