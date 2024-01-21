FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry update && poetry install

EXPOSE 8080

CMD ["poetry", "run", "python", "/app/main.py", "0.0.0.0:8080"]
