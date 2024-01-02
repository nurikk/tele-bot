FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/application

RUN pip install --no-cache-dir --trusted-host pypi.python.org pipenv

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --system --deploy --dev
COPY ./src ./src
COPY ./newrelic.ini ./
COPY bot.sh ./
COPY ./pyproject.toml ./
COPY ./migrations ./migrations
CMD ["./bot.sh"]
