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

# Create Python virtual environment
apt update -qq
apt install --yes -qq "$python_version" "$python_version-venv"
python3 -m venv "$venv_dir"

# Install the SORT Django app package
$pip install -r requirements.txt
cp --recursive * "$sort_dir/"

# Install Gunicorn service
cp --verbose config/systemd/gunicorn.service /etc/systemd/system/gunicorn.service
cp --verbose config/systemd/gunicorn.socket /etc/systemd/system/gunicorn.socket
systemctl daemon-reload
systemctl enable gunicorn.service
systemctl enable gunicorn.socket

# Install web reverse proxy server
# Install nginx
# https://nginx.org/en/docs/install.html
apt install --yes -qq nginx

# Configure web server
rm -f /etc/nginx/sites-enabled/default
cp config/nginx/*.conf /etc/nginx/sites-available
ln -s /etc/nginx/sites-available/gunicorn.conf /etc/nginx/sites-enabled/gunicorn.conf
