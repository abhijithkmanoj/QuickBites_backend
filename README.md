# QuickBites Backend

This is the FastAPI backend for the QuickBites food delivery platform.

## Setup

1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Create or update `backend/.env` with your environment values
4. Run locally: `poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Environment

- `backend/.env` contains the required default variables for local development.
- `DATABASE_URL` should point to a PostgreSQL instance in production.
- `SECRET_KEY` should be a secure random string.

## Database Setup

1. Create a PostgreSQL database.
2. Update `backend/.env` or your environment variables.
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
