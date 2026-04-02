#!/bin/bash
set -e

echo "Waiting for PostgreSQL at $POSTGRES_HOST..."
until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" >/dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL ready"

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

# Create cache table (if using database cache)
echo "Creating cache table..."
python manage.py createcachetable 2>/dev/null || true

echo "=========================================="
echo "Starting Uvicorn Server"
echo "=========================================="

# Start Gunicorn (WSGI)
exec uvicorn dogbuddy.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers ${UVICORN_WORKERS:-2} \
  --log-level info \
  --access-log \
  --proxy-headers \
  --forwarded-allow-ips '*'