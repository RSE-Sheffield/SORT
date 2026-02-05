#!/usr/bin/env bash
set -e

# SORT deployment script for Ubuntu 22.04 LTS
# See: How to deploy Django
# https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/#the-application-object

# Usage:
# Clone the repository
# git clone git@github.com:RSE-Sheffield/SORT.git
# cd SORT
# sudo bash -x scripts/deploy.sh

# Options
sort_dir="/opt/sort"
venv_dir="$sort_dir/venv"
pip="$venv_dir/bin/pip"
python_version="python$(cat .python-version | xargs)"
python="$venv_dir/bin/python"
env_file="$sort_dir/.env"
node_version=20
django_media_root="/srv/www/sort/uploads/"

# Install British UTF-8 locale so we can use this with PostgreSQL.
# This is important to avoid the limitations of the LATIN1 character set.
sudo locale-gen en_GB
sudo locale-gen en_GB.UTF-8
sudo update-locale

# Create Python virtual environment
mkdir --parents "$sort_dir"
apt update -qq
apt install --upgrade --yes -qq "$python_version" "$python_version-venv" curl
python3 -m venv "$venv_dir"

# Install the SORT Django app package
$pip install --quiet -r requirements.txt
# Ensure clean migrations from the repo
sudo rm -r "$sort_dir"/**/migrations
cp --recursive ./* "$sort_dir/"

# Create gunicorn group if it doesn't exist
if ! getent group gunicorn > /dev/null 2>&1; then
    groupadd --system gunicorn
fi

# Create gunicorn user if it doesn't exist
if ! getent passwd gunicorn > /dev/null 2>&1; then
    useradd --system --gid gunicorn --home-dir /nonexistent --no-create-home --shell /bin/false gunicorn
fi

# Create environment file
sudo touch "$env_file"
sudo chmod 600 "$env_file"

# Install Node.js package manager
# https://github.com/nodesource/distributions?tab=readme-ov-file#installation-instructions-deb
# Get the Ubuntu apt repository
echo "Installing Node..."
curl -fsSL "https://deb.nodesource.com/setup_$node_version.x" -o nodesource_setup.sh
sudo -E bash nodesource_setup.sh
apt-get install -y --allow-downgrades nodejs="$node_version.*"
node --version

# Install JavaScript package
# (Use a sub-shell to avoid changing directory.)
(cd "$sort_dir" && npm ci && npm audit fix && npm run build)

# Install static files into DJANGO_STATIC_ROOT
# This runs in a subshell because it's changing directory
(cd "$sort_dir" && exec $python manage.py collectstatic --no-input)

# Create uploads folder
sudo mkdir --parents "$django_media_root"

# Install Gunicorn service
echo "Installing Gunicorn service..."
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
echo "Installing NGINX..."
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
echo "Installing PostgreSQL..."
apt install --yes -qq postgresql
# Restart PostgreSQL to enable any new locales
systemctl restart postgresql

# Configure PostgreSQL database
echo "Configuring PostgreSQL database..."
# Get database credentials from environment or use defaults
db_name="${DJANGO_DATABASE_NAME:-sort}"
db_user="${DJANGO_DATABASE_USER:-sort}"
db_password="${DJANGO_DATABASE_PASSWORD:-$(openssl rand -base64 32)}"
db_schema="${db_name}"  # Use same name for schema as database

# Create database with proper encoding and locale
# See: docs/deployment.md
sudo -u postgres createdb --template=template0 --encoding=UTF8 --locale=en_GB.UTF-8 "$db_name" "SORT application" 2>/dev/null || echo "Database $db_name already exists"

# Create database user
sudo -u postgres createuser "$db_user" 2>/dev/null || echo "User $db_user already exists"

# Set user password and configure Django-recommended settings
sudo -u postgres psql "$db_name" <<-EOSQL
	-- Set password for the user
	ALTER USER $db_user WITH PASSWORD '$db_password';

	-- Create schema and set ownership
	CREATE SCHEMA IF NOT EXISTS $db_schema AUTHORIZATION $db_user;

	-- Restrict user to only see their schema
	ALTER ROLE $db_user SET SEARCH_PATH TO $db_schema;

	-- Configure Django-recommended settings
	ALTER ROLE $db_user SET client_encoding TO 'utf8';
	ALTER ROLE $db_user SET default_transaction_isolation TO 'read committed';
	ALTER ROLE $db_user SET timezone TO 'Europe/London';

	-- Grant necessary permissions
	GRANT CONNECT ON DATABASE $db_name TO $db_user;
	GRANT USAGE ON SCHEMA $db_schema TO $db_user;
	GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA $db_schema TO $db_user;
	ALTER DEFAULT PRIVILEGES FOR USER $db_user GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $db_user;
EOSQL

# Update environment file with database credentials
echo "Updating environment configuration..."
if ! grep -q "DJANGO_DATABASE_ENGINE" "$env_file"; then
    echo "DJANGO_DATABASE_ENGINE=django.db.backends.postgresql" >> "$env_file"
fi
if ! grep -q "DJANGO_DATABASE_NAME" "$env_file"; then
    echo "DJANGO_DATABASE_NAME=$db_name" >> "$env_file"
fi
if ! grep -q "DJANGO_DATABASE_USER" "$env_file"; then
    echo "DJANGO_DATABASE_USER=$db_user" >> "$env_file"
fi
if ! grep -q "DJANGO_DATABASE_PASSWORD" "$env_file"; then
    echo "DJANGO_DATABASE_PASSWORD=$db_password" >> "$env_file"
fi
if ! grep -q "DJANGO_DATABASE_HOST" "$env_file"; then
    echo "DJANGO_DATABASE_HOST=127.0.0.1" >> "$env_file"
fi
if ! grep -q "DJANGO_DATABASE_PORT" "$env_file"; then
    echo "DJANGO_DATABASE_PORT=5432" >> "$env_file"
fi

echo "Database credentials saved to $env_file"
echo "Database: $db_name"
echo "User: $db_user"
echo "Schema: $db_schema"

# Run deployment checks
echo "Checking Django system..."
# https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
(cd "$sort_dir" && exec $python manage.py check --deploy)

# Migrate database changes
# https://docs.djangoproject.com/en/5.1/topics/migrations/
echo "Applying Django migrations..."
(cd "$sort_dir" && $python manage.py migrate)
