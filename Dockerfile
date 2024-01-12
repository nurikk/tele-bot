FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /opt/application

RUN --mount=type=cache,target=~/.cache/pip pip install --trusted-host pypi.python.org pipenv

COPY Pipfile* .

RUN --mount=type=cache,target=~/.cache/pipenv pipenv install --system --deploy --dev
COPY ./src ./src
COPY bot.sh ./
COPY ./pyproject.toml ./
COPY ./migrations ./migrations
CMD ["./bot.sh"]
