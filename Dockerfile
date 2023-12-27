FROM python:3.11-slim

WORKDIR /opt/application

RUN pip install --no-cache-dir --trusted-host pypi.python.org pipenv

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --system --deploy --dev
COPY ./src ./src
COPY ./entrypoint.sh ./
COPY ./pyproject.toml ./
COPY ./migrations ./migrations
CMD ["./entrypoint.sh"]
