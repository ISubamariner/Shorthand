FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dev stage — used by docker-compose
FROM base AS dev
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Prod stage — used by Render
FROM base AS prod
RUN groupadd --system app && useradd --system --gid app --home /app app \
    && chown -R app:app /app
RUN python manage.py collectstatic --noinput 2>/dev/null || true
USER app
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_admin && python manage.py seed_symbols && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
