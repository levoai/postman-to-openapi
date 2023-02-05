FROM python:3.9 AS build-env

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev curl && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip

WORKDIR /app

FROM nikolaik/python-nodejs:python3.9-nodejs19-slim as node-builder

RUN npm i openapi-to-postmanv2 -g
RUN npm i postman-to-openapi -g

FROM build-env AS builder
WORKDIR /app/levo_postman

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    WHEELHOUSE_DIR=/app/wheels

# Install poetry separately to avoid conflicts with the project's dependencies
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.3.2 python3 -

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml

RUN $HOME/.local/bin/poetry export --without-hashes -f requirements.txt > requirements.txt
RUN /venv/bin/pip install -r requirements.txt --verbose

COPY ./src ./src
RUN $HOME/.local/bin/poetry build && /venv/bin/pip install dist/*.whl

# Build the final image!
FROM node-builder as final
WORKDIR /app/levo_postman
ENV PYTHONPATH=/venv/lib/python3.9/site-packages
ENV OPTIONS_FILE=/app/levo_postman/options.json

COPY --from=builder /venv /venv
COPY ./options.json ./options.json

CMD ["/venv/bin/gunicorn", "levo_postman.asgi:app", "-b", "0.0.0.0:80", "-k", "uvicorn.workers.UvicornWorker"]
