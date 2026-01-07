#!/usr/bin/env bash
# Export the entire Django database to a JSON file.

# Usage:
# bash scripts/export.sh

# Example:
# bash scripts/export.sh > sort-export-$(date -I).json

# Stop on errors
set -euo pipefail

# Django data export
# https://docs.djangoproject.com/en/5.2/ref/django-admin/#dumpdata

# Export entire database (apart from unwanted system data)
python manage.py dumpdata \
  --exclude auth.permission --exclude contenttypes --exclude admin.logentry --exclude sessions.session \
  --indent 2 --format json
