#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

if [[ "${SEED_DEMO_ON_DEPLOY:-false}" == "true" ]]; then
  python manage.py seed_demo
fi
