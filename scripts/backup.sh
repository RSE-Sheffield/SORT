#!/usr/bin/env bash
# One-time backup of SORT Online database
# This is an interactive script that requires the database password to be entered.

# Usage:
# bash scripts/backup.sh

# Stop on errors
set -e

# Options
BACKUP_DIR="$(mktemp --directory)"
DB_NAME="sort"
DB_USER="sort"
SORT_DIR="/opt/sort"
SORT_VENV="/opt/sort/venv"
python="$SORT_VENV/bin/python3"
LOG_FILE="$BACKUP_DIR/backup.log"
uploads_path="/srv/www/sort/uploads"

# Create backup folder
mkdir --parents "$BACKUP_DIR"
echo "Backing up to $BACKUP_DIR..."

# Write to log file (and to screen)
exec > >(tee -a "$LOG_FILE") 2>&1

# Backup PostgreSQL database (password prompt should appear)
echo "Backing up SQL database..."
pg_dump -U "$DB_USER" -h 127.0.0.1 "$DB_NAME" | gzip > "$BACKUP_DIR/sort-pg_dump.sql.gz"

# Django data export
# https://docs.djangoproject.com/en/5.2/ref/django-admin/#dumpdata
echo "Backing up Django data..."
# Use sudo so we can read .env
(cd "$SORT_DIR" && PYTHONIOENCODING=utf-8 sudo -E $python manage.py dumpdata --indent 2 | gzip > "$BACKUP_DIR/sort-django-dumpdata.json.gz")

# Backup uploaded media files
echo "Backing up media files..."
tar -czf "$BACKUP_DIR/sort-uploads.tar.gz" --directory "$uploads_path" .

# List what was backed up
echo ""
ls -lh "$BACKUP_DIR"
