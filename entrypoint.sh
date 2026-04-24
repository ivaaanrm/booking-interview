#!/bin/sh
set -e

uv run manage.py migrate --noinput
uv run manage.py collectstatic --noinput --clear

exec "$@"
