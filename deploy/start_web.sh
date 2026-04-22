#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"

cd "$PROJECT_DIR"

if [[ ! -f "$PROJECT_DIR/.env" ]]; then
  echo ".env topilmadi: $PROJECT_DIR/.env" >&2
  exit 1
fi

set -a
source "$PROJECT_DIR/.env"
set +a

source "$VENV_DIR/bin/activate"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind "${GUNICORN_BIND:-0.0.0.0:8003}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
