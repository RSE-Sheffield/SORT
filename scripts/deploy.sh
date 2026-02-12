#!/usr/bin/env bash
set -e

# SORT deployment script for Ubuntu 22.04 LTS
# Please read
# https://github.com/RSE-Sheffield/SORT/blob/main/docs/deployment.md

# Usage:
# Clone the repository
# git clone git@github.com:RSE-Sheffield/SORT.git
# cd SORT
# sudo bash scripts/deploy.sh
# If you need more verbosity, use the -x option
# sudo bash -x scripts/deploy.sh

# Options
sort_dir="/opt/sort"
venv_dir="$sort_dir/venv"
python_version="python$(cat .python-version | xargs)"
python="$venv_dir/bin/python"
pip="$venv_dir/bin/python -m pip"
env_file="$sort_dir/.env"
node_version=20
django_media_root="/srv/www/sort/uploads/"

# Install British UTF-8 locale so we can use this with PostgreSQL.
# This is important to avoid the limitations of the LATIN1 character set.
sudo locale-gen en_GB
sudo locale-gen en_GB.UTF-8
sudo update-locale

# Install OS packages (don't ask for user input)
echo "Installing Ubuntu packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
apt-get install -y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" "$python_version" "$python_version-venv" curl

# Create program files directory
mkdir --parents "$sort_dir"

# Create Python virtual environment
echo "Installing Python packages..."
# If the virtual environment doesn't already exist, make a new one
if [ ! -f "$venv_dir/pyvenv.cfg" ]; then
    python3 -m venv "$venv_dir"
fi

# Install the SORT Django app package
$python -m pip install --upgrade pip
$pip install --quiet --upgrade -r requirements.txt
cp --recursive ./* "$sort_dir/"

# Create gunicorn group if it doesn't exist
echo "Creating system user..."
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
npm config set fund false

# Upgrade npm to latest stable version
# https://github.com/RSE-Sheffield/SORT/issues/494
echo "Upgrading npm to latest stable version..."
npm install -g npm@latest
npm --version

# Install JavaScript package
echo "Installing front-end packages..."
# (Use a sub-shell to avoid changing directory.)
(cd "$sort_dir" && npm ci && npm run build)

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

# Check if password already exists in .env file, if not generate a new one
if [ -f "$env_file" ] && grep -q "^DJANGO_DATABASE_PASSWORD=" "$env_file"; then
    # Extract existing password from .env file
    db_password=$(grep "^DJANGO_DATABASE_PASSWORD=" "$env_file" | cut -d'=' -f2-)

    # Validate password is not empty
    if [ -z "$db_password" ]; then
        echo "ERROR: DJANGO_DATABASE_PASSWORD in $env_file is empty or invalid"
        echo "Please set a valid password in $env_file or remove the line to generate a new one"
        exit 1
    fi

    echo "Using existing database password from $env_file"
else
    # Generate new password (check env var first, then generate)
    db_password="${DJANGO_DATABASE_PASSWORD:-$(openssl rand -base64 32)}"
    echo "Generated new database password"
fi

db_schema="${db_name}"  # Use same name for schema as database

# Create database with proper encoding and locale
# See: docs/deployment.md
sudo -u postgres createdb --template=template0 --encoding=UTF8 --locale=en_GB.UTF-8 "$db_name" "SORT application" 2>/dev/null || echo "Database $db_name already exists"

# Check if database user exists
user_exists=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'" 2>/dev/null)
if [ "$user_exists" = "1" ]; then
    user_is_new=false
else
    echo "Creating new database user: $db_user"
    sudo -u postgres createuser "$db_user"
    user_is_new=true
fi

# Configure user settings and permissions (safe to run idempotently)
# Only set password for NEW users to avoid overwriting existing passwords
if [ "$user_is_new" = true ]; then
    echo "Setting password for new database user..."
    sudo -u postgres psql "$db_name" -c "ALTER USER $db_user WITH PASSWORD '$db_password';"
fi

# Apply common database configuration (idempotent operations)
sudo -u postgres psql "$db_name" <<-EOSQL
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
# Helper function to set or update environment variable
update_env_var() {
    local key=$1
    local value=$2
    if grep -q "^${key}=" "$env_file" 2>/dev/null; then
        # Update existing value
        sed -i "s|^${key}=.*|${key}=${value}|" "$env_file"
    else
        # Add new value
        echo "${key}=${value}" >> "$env_file"
    fi
}

update_env_var "DJANGO_DATABASE_ENGINE" "django.db.backends.postgresql"
update_env_var "DJANGO_DATABASE_NAME" "$db_name"
update_env_var "DJANGO_DATABASE_USER" "$db_user"
update_env_var "DJANGO_DATABASE_HOST" "127.0.0.1"
update_env_var "DJANGO_DATABASE_PORT" "5432"

# Only write password to .env if it's a new user or password doesn't exist in .env
if [ "$user_is_new" = true ] || ! grep -q "^DJANGO_DATABASE_PASSWORD=" "$env_file" 2>/dev/null; then
    update_env_var "DJANGO_DATABASE_PASSWORD" "$db_password"
    echo "Database password written to $env_file"
fi

echo "Database credentials saved to $env_file"
echo "Database: $db_name"
echo "User: $db_user"
echo "Schema: $db_schema"

# Test database connection
echo "Testing database connection..."
if ! PGPASSWORD="$db_password" psql -h 127.0.0.1 -U "$db_user" -d "$db_name" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "ERROR: Database connection test failed"
    echo "Please check:"
    echo "  1. PostgreSQL is running: systemctl status postgresql"
    echo "  2. Database credentials in $env_file"
    echo "  3. PostgreSQL authentication settings in /etc/postgresql/*/main/pg_hba.conf"
    exit 1
fi
echo "Database connection successful"

# Run deployment checks
echo "Checking Django system..."
# https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
# shellcheck source=/opt/sort/.env
(cd "$sort_dir" && set -a && source "$env_file" && set +a && exec $python manage.py check --deploy)

# Migrate database changes
# https://docs.djangoproject.com/en/5.1/topics/migrations/
echo "Applying Django migrations..."
# shellcheck source=/opt/sort/.env
(cd "$sort_dir" && set -a && source "$env_file" && set +a && $python manage.py migrate)

# Ensure updated code is loaded
echo "Restarting web application service..."
systemctl restart gunicorn.service
