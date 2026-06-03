# QuickBites Backend

This is the FastAPI backend for the QuickBites food delivery platform.

## Setup

1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Copy `.env.example` to `.env` and update values
4. Run locally: `poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Environment

- `.env.example` contains the required default variables.
- `DATABASE_URL` should point to a PostgreSQL instance.
- `SECRET_KEY` should be a secure random string.

## Database Setup

1. Create a PostgreSQL database.
2. Copy `.env.example` to `.env`.
3. Set `DATABASE_URL` to your database connection string.

## Database Migrations

From the `backend` folder:

- `poetry run alembic revision --autogenerate -m "initial"`
- `poetry run alembic upgrade head`

## Seed Data

Run:

- `poetry run python -m app.db.seed`

## Endpoints

- `GET /healthz` — Kubernetes-style health probe
- `GET /api/v1/health` — application health check
- `GET /api/v1/welcome` — welcome message
