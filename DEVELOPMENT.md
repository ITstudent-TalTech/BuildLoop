# Development Quickstart

## 1) Create environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## 2) Configure environment

Set `DATABASE_URL` if you are not using the default local value.

```bash
export DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/buildloop'
```

## 3) Run migrations

```bash
alembic upgrade head
```

## 4) Run API

```bash
uvicorn app.main:app --reload
```

Health endpoint:

```bash
curl http://127.0.0.1:8000/v1/health
```
