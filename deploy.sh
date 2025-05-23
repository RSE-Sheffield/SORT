#!/usr/bin/env bash
set -e

# SORT deployment script for Ubuntu 22.04 LTS
# See: How to deploy Django
# https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/#the-application-object

# Usage:
# Clone the repository
# git clone git@github.com:RSE-Sheffield/SORT.git
# cd SORT
# sudo bash -x deploy.sh

# Options
sort_dir="/opt/sort"
venv_dir="$sort_dir/venv"
pip="$venv_dir/bin/pip"
python_version="python3.12"
python="$venv_dir/bin/python"
env_file="$sort_dir/.env"
django_media_root="/srv/www/sort/uploads/"

# Install British UTF-8 locale so we can use this with PostgreSQL.
# This is important to avoid the limitations of the LATIN1 character set.
sudo locale-gen en_GB
sudo locale-gen en_GB.UTF-8
sudo update-locale

# Create Python virtual environment
mkdir --parents "$sort_dir"
apt update -qq
apt install --upgrade --yes -qq "$python_version" "$python_version-venv"
python3 -m venv "$venv_dir"

# Install the SORT Django app package
$pip install --quiet -r requirements.txt
sudo rm -r "$sort_dir"/**/migrations
cp --recursive ./* "$sort_dir/"

# Create environment file
sudo touch "$env_file"
sudo chmod 600 "$env_file"

# Install static files into DJANGO_STATIC_ROOT
# This runs in a subshell because it's changing directory
(cd "$sort_dir" && exec $python manage.py collectstatic --no-input)

# Create uploads folder
sudo mkdir --parents "$django_media_root"

# Install Gunicorn service
cp --verbose config/systemd/gunicorn.service /etc/systemd/system/gunicorn.service
cp --verbose config/systemd/gunicorn.socket /etc/systemd/system/gunicorn.socket
systemctl daemon-reload
systemctl enable gunicorn.service
systemctl enable gunicorn.socket
systemctl start gunicorn.service
systemctl reload gunicorn.service
systemctl restart gunicorn.service

# Install web reverse proxy server
# Install nginx
# https://nginx.org/en/docs/install.html
apt install --yes -qq nginx
nginx -version

# Configure web server
rm -f /etc/nginx/sites-enabled/default
cp config/nginx/*.conf /etc/nginx/sites-available
# Enable the site by creating a symbolic link
ln --symbolic --force /etc/nginx/sites-available/gunicorn.conf /etc/nginx/sites-enabled/gunicorn.conf
systemctl reload nginx.service

# Install PostgreSQL database
# https://ubuntu.com/server/docs/install-and-configure-postgresql
apt install --yes -qq postgresql
# Restart PostgreSQL to enable any new locales
systemctl restart postgresql

# Run deployment checks
# https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
(cd "$sort_dir" && exec $python manage.py check --deploy)
