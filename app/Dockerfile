# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS runtime

# System packages: build-essential for any wheels that need to compile,
# libpq for asyncpg, curl for healthchecks if you add them later.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# We arrange the in-container layout so that `app` is a proper top-level
# Python package. Railway's "root directory" = /app/ means the build
# context is the contents of /repo/app/. We place that under /code/app/
# inside the container, putting /code/ on PYTHONPATH so `import app.foo`
# resolves correctly.
WORKDIR /code

# Step 1: copy pyproject first for layer caching. Dependencies don't
# reinstall on every code change.
COPY pyproject.toml /code/app/pyproject.toml

# Step 2: install runtime dependencies. We can't use `pip install -e .`
# here because source isn't copied yet, and we don't want dev deps
# (pytest, mypy, ruff) in the production image.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "sqlalchemy[asyncio]>=2.0" \
    "asyncpg>=0.29.0" \
    "alembic>=1.13.0" \
    "pydantic-settings>=2.5.0" \
    "supabase>=2.0.0" \
    "python-multipart>=0.0.9" \
    "httpx>=0.27.0" \
    "pypdf>=4.0.0" \
    "pdfplumber>=0.11.0"

# Step 3: copy the application source. Layer cache breaks here when
# source changes — fast subsequent builds.
COPY . /code/app/

ENV PYTHONPATH=/code \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Railway sets $PORT. Default to 8000 for local docker-run.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
