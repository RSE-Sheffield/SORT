#!/bin/bash
set -e

echo "Checking for missing migrations..."
python manage.py makemigrations --check --dry-run

# Backend tests (Django)
python manage.py test home/tests --parallel=auto --failfast
python manage.py test survey/tests --parallel=auto --failfast
