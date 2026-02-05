# Troubleshooting

This guide covers common issues, debugging techniques, and how to find logs for the SORT application.

## Finding Logs

### Development Environment

**Django development server**

When running `python manage.py runserver`, logs appear directly in the terminal. Set the log level in your `.env` file:

```bash
DJANGO_LOG_LEVEL=DEBUG
```

**Vite development server**

Frontend build errors and warnings appear in the terminal running `npm run dev`.

### Production Environment

**Gunicorn logs (Django application)**

```bash
sudo journalctl -u gunicorn.service --follow
```

View recent logs:

```bash
sudo journalctl -u gunicorn.service --since "1 hour ago"
```

Filter by priority (errors only):

```bash
sudo journalctl -u gunicorn.service -p err
```

**nginx logs (web server)**

Access log (successful requests):

```bash
sudo tail --follow /var/log/nginx/access.log
```

Error log (failures and warnings):

```bash
sudo tail --follow /var/log/nginx/error.log
```

**PostgreSQL logs**

```bash
sudo journalctl -u postgresql --follow
```

Or check the PostgreSQL log directory:

```bash
sudo ls -la /var/log/postgresql/
sudo tail /var/log/postgresql/postgresql-*-main.log
```

**systemd service logs**

```bash
sudo journalctl -u nginx.service
sudo journalctl -u gunicorn.socket
```

## Service Status

Check if services are running:

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql
```

A healthy output shows `Active: active (running)`. If a service shows `failed` or `inactive`, check the logs above for details.

## Common Issues

### Application Won't Start

#### "502 Bad Gateway" in browser

The Django application isn't running or can't be reached.

1. Check Gunicorn status:
   ```bash
   sudo systemctl status gunicorn
   ```

2. If stopped, start it:
   ```bash
   sudo systemctl start gunicorn
   ```

3. If it fails to start, check logs:
   ```bash
   sudo journalctl -u gunicorn.service -n 50
   ```

4. Verify the socket exists:
   ```bash
   ls -la /run/gunicorn.sock
   ```

#### "500 Internal Server Error"

An unhandled exception in the Django application.

1. Check Gunicorn logs for the Python traceback:
   ```bash
   sudo journalctl -u gunicorn.service --since "5 minutes ago"
   ```

2. Common causes:
   - Missing environment variables in `/opt/sort/.env`
   - Database connection issues
   - Missing migrations
   - File permission problems

#### Application starts but pages don't load correctly

1. Verify static files are collected:
   ```bash
   ls -la /var/www/sort/static/
   ```

2. If missing, run:
   ```bash
   cd /opt/sort
   sudo /opt/sort/venv/bin/python manage.py collectstatic --no-input
   ```

3. Verify nginx is serving static files (check nginx error log for 404s on `/static/` paths)

### Database Issues

#### "Connection refused" or "Could not connect to server"

PostgreSQL isn't running or is misconfigured.

1. Check PostgreSQL status:
   ```bash
   sudo systemctl status postgresql
   ```

2. Start if not running:
   ```bash
   sudo systemctl start postgresql
   ```

3. Verify database exists:
   ```bash
   sudo -u postgres psql --list
   ```

4. Check credentials in `/opt/sort/.env` match the database user

#### "Relation does not exist" or missing tables

Migrations haven't been run.

```bash
cd /opt/sort
sudo /opt/sort/venv/bin/python manage.py migrate
```

#### "Permission denied for schema" or "Permission denied for table"

Database user lacks required permissions.

```bash
sudo -u postgres psql sort
```

Then run:

```sql
GRANT USAGE ON SCHEMA sort TO sort;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sort TO sort;
ALTER DEFAULT PRIVILEGES FOR USER sort GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sort;
```

#### Database encoding issues

If you see character encoding errors, ensure the database was created with UTF-8:

```bash
sudo -u postgres psql -c "SELECT datname, pg_encoding_to_char(encoding) FROM pg_database WHERE datname = 'sort';"
```

Should show `UTF8`. If not, you may need to recreate the database (see [deployment.md](deployment.md#create-a-database)).

### Authentication Issues

#### Users can't log in

1. Check email backend configuration in `.env`:
   ```bash
   grep EMAIL /opt/sort/.env
   ```

2. For development, use the console backend:
   ```bash
   DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   ```

3. Check if the user exists and is active:
   ```bash
   cd /opt/sort
   sudo /opt/sort/venv/bin/python manage.py shell
   ```
   ```python
   from home.models import User
   User.objects.filter(email='user@example.com').values('is_active', 'email')
   ```

#### "CSRF verification failed"

1. Ensure `DJANGO_ALLOWED_HOSTS` in `.env` includes the server's hostname
2. Check that cookies are being sent (HTTPS required in production)
3. Verify `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` match your HTTPS setup

#### Password reset emails not arriving

1. Check email configuration in `.env`
2. Test email sending:
   ```bash
   cd /opt/sort
   sudo /opt/sort/venv/bin/python manage.py shell
   ```
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```
3. Check spam folders
4. Review Gunicorn logs for email sending errors

### File Upload Issues

#### "Permission denied" when uploading files

1. Check upload directory permissions:
   ```bash
   ls -la /srv/www/sort/uploads/
   ```

2. Fix permissions:
   ```bash
   sudo chown -R gunicorn:gunicorn /srv/www/sort/uploads/
   sudo chmod -R 755 /srv/www/sort/uploads/
   ```

3. Ensure the systemd service has `ReadWritePaths` configured (check `gunicorn.service`)

#### "Request entity too large" (413 error)

File exceeds nginx's upload limit.

1. Check current limit in nginx config:
   ```bash
   grep client_max_body_size /etc/nginx/sites-enabled/*
   ```

2. Increase if needed (in the server block):
   ```nginx
   client_max_body_size 10m;
   ```

3. Reload nginx:
   ```bash
   sudo systemctl reload nginx
   ```

### Frontend/JavaScript Issues

#### Svelte components not loading

1. Check browser console for JavaScript errors (F12 → Console tab)

2. In development, ensure Vite is running:
   ```bash
   npm run dev
   ```

3. In production, ensure assets are built:
   ```bash
   cd /opt/sort
   npm run build
   sudo /opt/sort/venv/bin/python manage.py collectstatic --no-input
   ```

4. Check for 404 errors on `/static/ui-components/` paths in nginx logs

#### "Vite manifest not found"

The frontend hasn't been built for production.

```bash
cd /opt/sort
npm run build
```

Verify manifest exists:

```bash
ls -la /opt/sort/static/ui-components/manifest.json
```

### SSL/HTTPS Issues

#### "SSL certificate problem" or browser security warnings

1. Check certificate validity:
   ```bash
   openssl x509 -in /etc/ssl/certs/sort.crt -text -noout | grep -A2 Validity
   ```

2. Verify certificate matches the domain:
   ```bash
   openssl x509 -in /etc/ssl/certs/sort.crt -text -noout | grep Subject:
   ```

3. Check certificate chain is complete

4. Ensure private key matches certificate:
   ```bash
   openssl x509 -noout -modulus -in /etc/ssl/certs/sort.crt | openssl md5
   openssl rsa -noout -modulus -in /etc/ssl/private/sort.key | openssl md5
   ```
   Both MD5 hashes should match.

### Performance Issues

#### Slow page loads

1. Check server resources:
   ```bash
   top
   free -h
   df -h
   ```

2. Check database query performance:
   - Enable Django Debug Toolbar in development
   - Look for N+1 query problems

3. Check nginx access logs for slow endpoints:
   ```bash
   # Add $request_time to nginx log format, then:
   awk '{print $NF, $7}' /var/log/nginx/access.log | sort -rn | head -20
   ```

#### High memory usage

1. Check Gunicorn worker count (default may be too high)

2. Monitor memory per worker:
   ```bash
   ps aux | grep gunicorn
   ```

3. Consider reducing workers or adding `--max-requests` to recycle workers

## Debugging Techniques

### Enable Django Debug Mode (Development Only)

In `.env`:

```bash
DJANGO_DEBUG=True
DJANGO_LOG_LEVEL=DEBUG
```

**Never enable DEBUG in production** - it exposes sensitive information.

### Django Debug Toolbar

In development with `DEBUG=True`, the debug toolbar appears on the right side of pages, showing:

- SQL queries executed
- Template rendering time
- Request/response headers
- Cache usage

### Interactive Django Shell

```bash
cd /opt/sort
sudo /opt/sort/venv/bin/python manage.py shell
```

Useful for:

```python
# Check a user's organisation membership
from home.models import User, OrganisationMembership
user = User.objects.get(email='user@example.com')
OrganisationMembership.objects.filter(user=user).select_related('organisation')

# Check survey configuration
from survey.models import Survey
survey = Survey.objects.get(pk=1)
survey.survey_config  # View the JSON configuration

# Test service layer methods
from survey.services import survey_service
survey_service.get_survey(user, survey.pk)
```

### Database Queries

Connect to the database directly:

```bash
cd /opt/sort
sudo /opt/sort/venv/bin/python manage.py dbshell
```

Useful queries:

```sql
-- List all tables
\dt

-- Check survey responses
SELECT id, survey_id, created_at FROM sort.survey_surveyresponse ORDER BY created_at DESC LIMIT 10;

-- Check user permissions
SELECT u.email, om.role, o.name
FROM sort.home_user u
JOIN sort.home_organisationmembership om ON om.user_id = u.id
JOIN sort.home_organisation o ON o.id = om.organisation_id;
```

### Test Email Configuration

```bash
cd /opt/sort
sudo /opt/sort/venv/bin/python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

print(f"Backend: {settings.EMAIL_BACKEND}")
print(f"Host: {settings.EMAIL_HOST}")
print(f"Port: {settings.EMAIL_PORT}")

# Send test email
send_mail(
    'SORT Test Email',
    'This is a test email from SORT.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@example.com'],
    fail_silently=False,
)
```

### Check Environment Variables

```bash
# View all DJANGO_ variables (be careful - may contain secrets)
cd /opt/sort
sudo /opt/sort/venv/bin/python -c "import os; [print(k,v) for k,v in os.environ.items() if 'DJANGO' in k]"
```

Or in Django shell:

```python
from django.conf import settings
settings.DEBUG
settings.ALLOWED_HOSTS
settings.DATABASES['default']['NAME']
```

## Recovery Procedures

### Restart All Services

```bash
sudo systemctl restart postgresql
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Reset a User's Password

```bash
cd /opt/sort
sudo /opt/sort/venv/bin/python manage.py changepassword user@example.com
```

### Clear Orphaned Upload Files

```bash
cd /opt/sort
sudo /opt/sort/venv/bin/python manage.py clear_orphaned_files
```

### Rebuild Frontend Assets

```bash
cd /opt/sort
npm ci
npm run build
sudo /opt/sort/venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart gunicorn
```

### Database Backup and Restore

**Backup:**

```bash
sudo -u postgres pg_dump sort > sort_backup_$(date +%Y%m%d).sql
```

**Restore:**

```bash
sudo -u postgres psql sort < sort_backup_20240115.sql
```

## Getting Help

If you've exhausted these troubleshooting steps:

1. Check the [GitHub Issues](https://github.com/RSE-Sheffield/SORT/issues) for similar problems
2. Gather relevant log excerpts and error messages
3. Create a new issue with:
   - Steps to reproduce
   - Expected vs actual behaviour
   - Relevant log output
   - Environment details (OS version, browser, etc.)
