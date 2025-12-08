#!/usr/bin/env bash
# One-time backup of SORT Online database
# This is an interactive script that requires the database password to be entered.

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

# Create backup folder
mkdir --parents "$BACKUP_DIR"

# Write to log file (and to screen)
exec > >(tee -a "$LOG_FILE") 2>&1

# Backup PostgreSQL database (password prompt should appear)
echo "Backing up SQL database..."
pg_dump -U "$DB_USER" "$DB_NAME" --password | gzip > "$BACKUP_DIR/sort-db.sql.gz"

# Django data export
# https://docs.djangoproject.com/en/5.2/ref/django-admin/#dumpdata
echo "Backing up Django data..."
(cd "$SORT_DIR" && $python manage.py dumpdata --indent 2 | gzip > "$BACKUP_DIR/sort-django-dumpdata.json.gz")

# Backup uploaded media files
echo "Backing up media files..."
tar -czf "$BACKUP_DIR/sort-uploads.tar.gz" --directory /opt/sort uploads/

# List what was backed up
echo ""
ls -lh "$BACKUP_DIR"
