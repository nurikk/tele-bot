# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11.7
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim as base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

RUN --mount=type=cache,target=/root/.cache/pip pip install --trusted-host pypi.python.org pipenv

RUN --mount=type=cache,target=/root/.cache/pipenv \
    --mount=type=bind,source=Pipfile,target=Pipfile \
    --mount=type=bind,source=Pipfile.lock,target=Pipfile.lock \
    pipenv install --system --deploy

USER appuser
COPY . .
CMD ["./bot.sh"]
