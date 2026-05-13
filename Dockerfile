FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pip setuptools wheel

COPY pyproject.toml .
RUN mkdir -p mdmo && touch mdmo/__init__.py && \
    pip install --no-cache-dir lxml httpx pyyaml apscheduler aiosqlite && \
    pip install --no-cache-dir fastapi uvicorn "sqlalchemy[asyncio]>=2.0" jinja2 pydantic pydantic-settings

COPY mdmo/ mdmo/
COPY config.yaml .
RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "mdmo.main:app", "--host", "0.0.0.0", "--port", "8000"]
