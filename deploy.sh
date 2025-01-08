#!/usr/bin/env bash
st -e

# SORT deployment script for Ubuntu 22.04 LTS
# See: How to deploy Django
# https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/#the-application-object

# Usage:
# Clone the repository
# git clone git@github.com:RSE-Sheffield/SORT.git
# cd SORT
# sudo bash deploy.sh

# Options
venv_dir="/opt/sort/venv"
pip="$venv_dir/bin/pip"
python_version="python3.12"

# Create Python virtual environment
apt install --yes -qq "$python_version" "$python_version-venv"
python3 -m venv "$venv_dir"

# Install the SORT Django app package
$pip install .

# Install web reverse proxy server
# Install nginx
# https://nginx.org/en/docs/install.html
apt install --yes -qq nginx

# Configure web server
