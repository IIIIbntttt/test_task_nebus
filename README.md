# Async Payments Processing Service

Асинхронный микросервис для обработки платежей:
- `POST /api/v1/payments` принимает заявку на платеж (с `Idempotency-Key`).
- Платеж сохраняется в БД со статусом `pending`.
- Событие пишется в `outbox`.
- Outbox worker публикует событие в RabbitMQ (`payments.new`).
- Consumer обрабатывает платеж (эмуляция шлюза 2-5 сек, 90%/10%), обновляет статус, отправляет webhook.
- При ошибках webhook выполняется retry с backoff и публикацией в `payments.dlq` после исчерпания попыток.

## Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async + Alembic
- PostgreSQL
- RabbitMQ + FastStream
- Dishka (DI container)
- Docker + docker-compose
- uv + mypy + ruff + pytest

## Архитектура

Вертикальные срезы в формате `payments/<functional>/...`:

- `payments/create_payment`
- `payments/get_payment`
- `payments/process_payment`
- `payments/outbox`
- `payments/webhook`
- `payments/shared`

DI для HTTP-слоя построен через Dishka контейнер (`payments/shared/di.py`) и интеграцию с FastAPI.

## Local Run (uv)

1. Установить зависимости:

```bash
uv sync
```

2. Экспортировать переменные:

```bash
export APP_API_KEY=change-me
export APP_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/payments
export APP_RABBITMQ_URL=amqp://guest:guest@localhost:5672/
export APP_WEBHOOK_TIMEOUT_SECONDS=5
export PYTHONPATH=src
```

3. Применить миграции:

```bash
uv run alembic upgrade head
```

4. Запустить API:

```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

5. Запустить consumer:

```bash
uv run faststream run consumer_app:app
```

6. Запустить outbox worker:

```bash
uv run python src/outbox_worker_app.py
```

## Docker Compose

```bash
docker compose up --build
```

Сервисы:
- `postgres`
- `rabbitmq`
- `migrate` (init-сервис, выполняет `alembic upgrade head`)
- `api`
- `consumer`
- `outbox-worker`

## API Examples

Создать платеж:

```bash
curl -X POST 'http://localhost:8000/api/v1/payments' \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: change-me' \
  -H 'Idempotency-Key: order-123' \
  -d '{
    "amount": "100.00",
    "currency": "USD",
    "description": "Order #123",
    "metadata": {"order_id": "123"},
    "webhook_url": "https://example.com/webhook"
  }'
```

Получить платеж:

```bash
curl -X GET 'http://localhost:8000/api/v1/payments/<payment_id>' \
  -H 'X-API-Key: change-me'
```

## Idempotency

- `Idempotency-Key` обязателен.
- Повторный `POST` с тем же ключом возвращает уже созданный платеж, без дублей.

## Очереди и DLQ

- `payments.new` — события новых платежей.
- `payments.dlq` — сообщения, которые не удалось доставить в webhook после retry-цикла.

## Quality Gates

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
```

## Poe Tasks

```bash
uv run poe compose        # docker compose up --build -d
uv run poe compose_down   # docker compose down
uv run poe test           # pytest -q
uv run poe lint           # ruff + mypy
```
