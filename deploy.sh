#!/usr/bin/env bash
set -e

# SORT deployment script for Ubuntu 22.04 LTS
# See: How to deploy Django
# https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/#the-application-object

# Usage:
# Clone the repository
# git clone git@github.com:RSE-Sheffield/SORT.git
# cd SORT
# sudo bash deploy.sh

# Options
sort_dir="/opt/sort"
venv_dir="$sort_dir/venv"
pip="$venv_dir/bin/pip"
python_version="python3.12"

# Create Python virtual environment
apt update
apt install --yes -qq "$python_version" "$python_version-venv"
python3 -m venv "$venv_dir"

# Install the SORT Django app package
$pip install -r requirements.txt
cp --recursive * "$sort_dir/"

# Install Gunicorn service
cp --verbose config/systemd/gunicorn.service /etc/systemd/system/gunicorn.service

# Install web reverse proxy server
# Install nginx
# https://nginx.org/en/docs/install.html
apt install --yes -qq nginx
rm -f /etc/nginx/sites-enabled/default

# Configure web server
