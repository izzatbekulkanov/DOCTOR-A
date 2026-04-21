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

exec python manage.py run_telegram_bot \
  --poll-timeout "${BOT_POLL_TIMEOUT:-10}" \
  --sleep "${BOT_POLL_SLEEP:-1}"
