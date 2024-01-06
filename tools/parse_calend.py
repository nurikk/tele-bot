import json

from requests_html2 import HTMLSession


def parse_country(country: str, country_code: str):
    holidays = []
    url = f'https://www.calend.ru/holidays/{country}/'
    with HTMLSession() as session:
        response = session.get(url)
        elements = response.html.find(".datesList > ul > li")
        for el in elements:
            date_num = el.find('.dataNum > a > .number').select(lambda e: e.text, first=True, default="")
            date_month = el.find('.dataNum > a > .desc > .title').select(lambda e: e.text, first=True, default="")
            titles = el.find('.caption > .title').select(lambda e: e.text, default=[])
            holidays.append({
                'date_num': date_num,
                'date_month': date_month,
                'titles': titles
            })

    with open(f'../src/holidays/{country_code}.json', 'w') as f:
        f.write(json.dumps(holidays))


if __name__ == "__main__":
    parse_country('russtate', 'ru')
