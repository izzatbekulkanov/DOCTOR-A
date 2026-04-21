#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(whoami)}}"
SERVICE_GROUP="${SERVICE_GROUP:-$(id -gn "$SERVICE_USER")}"
DOMAIN="${DOMAIN:-${1:-_}}"
GUNICORN_BIND="${GUNICORN_BIND:-127.0.0.1:8001}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"

if [[ ! -f "$PROJECT_DIR/.env" ]]; then
  cp -n "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  echo ".env yaratildi. Avval qiymatlarni to'ldiring, keyin scriptni qayta ishga tushiring." >&2
  exit 1
fi

set -a
source "$PROJECT_DIR/.env"
set +a

SUDO=""
if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
fi

$SUDO apt-get update
$SUDO apt-get install -y python3-venv python3-pip build-essential libpq-dev nginx

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "$PROJECT_DIR/requirements.txt"

mkdir -p "$PROJECT_DIR/staticfiles" "$PROJECT_DIR/media"

python "$PROJECT_DIR/manage.py" migrate --noinput
python "$PROJECT_DIR/manage.py" collectstatic --noinput

WEB_TMP="$(mktemp)"
BOT_TMP="$(mktemp)"
NGINX_TMP="$(mktemp)"

sed \
  -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  -e "s|__SERVICE_USER__|$SERVICE_USER|g" \
  -e "s|__SERVICE_GROUP__|$SERVICE_GROUP|g" \
  "$PROJECT_DIR/deploy/doctor-a-web.service.template" > "$WEB_TMP"

sed \
  -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  -e "s|__SERVICE_USER__|$SERVICE_USER|g" \
  -e "s|__SERVICE_GROUP__|$SERVICE_GROUP|g" \
  "$PROJECT_DIR/deploy/doctor-a-bot.service.template" > "$BOT_TMP"

sed \
  -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  -e "s|__DOMAIN__|$DOMAIN|g" \
  -e "s|__GUNICORN_BIND__|$GUNICORN_BIND|g" \
  "$PROJECT_DIR/deploy/nginx-doctor-a.conf.template" > "$NGINX_TMP"

$SUDO install -m 0644 "$WEB_TMP" /etc/systemd/system/doctor-a-web.service
$SUDO install -m 0644 "$BOT_TMP" /etc/systemd/system/doctor-a-bot.service
$SUDO install -m 0644 "$NGINX_TMP" /etc/nginx/sites-available/doctor-a.conf
$SUDO ln -sf /etc/nginx/sites-available/doctor-a.conf /etc/nginx/sites-enabled/doctor-a.conf
$SUDO rm -f /etc/nginx/sites-enabled/default

rm -f "$WEB_TMP" "$BOT_TMP" "$NGINX_TMP"

$SUDO nginx -t
$SUDO systemctl daemon-reload
$SUDO systemctl enable doctor-a-web.service doctor-a-bot.service
$SUDO systemctl restart doctor-a-web.service
$SUDO systemctl restart doctor-a-bot.service
$SUDO systemctl restart nginx

echo "Deploy yakunlandi."
echo "Web service: doctor-a-web.service"
echo "Bot service: doctor-a-bot.service"
echo "Nginx site: /etc/nginx/sites-available/doctor-a.conf"
