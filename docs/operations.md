# Operations

This guide covers day-to-day management of an **already-running** production server: controlling services, viewing logs, and running Django management commands.

* If you're standing up a new server, see [deployment.md](deployment.md).
* If something is broken and you need to diagnose it, see [troubleshooting.md](troubleshooting.md).

Commands below assume the following shell setup, consistent with the other guides:

```bash
sort_dir="/opt/sort"
venv_dir="$sort_dir/venv"
python="$venv_dir/bin/python"
django_admin="$python $sort_dir/manage.py"

cd "$sort_dir"
```

# Services at a glance

| Unit | Type | Purpose | Config file |
|---|---|---|---|
| `gunicorn.socket` | socket | Listens on `/run/gunicorn.sock` and activates `gunicorn.service` on demand | [`config/systemd/gunicorn.socket`](../config/systemd/gunicorn.socket) |
| `gunicorn.service` | service | Runs the Django application via [Gunicorn](https://docs.gunicorn.org/) (WSGI) | [`config/systemd/gunicorn.service`](../config/systemd/gunicorn.service) |
| `nginx.service` | service | Reverse proxy, TLS termination, and static file serving | `/etc/nginx/sites-enabled/*` |
| `postgresql.service` | service | The database | distro-managed |

# Controlling services

## Restart vs reload

* `systemctl restart` stops and starts a fresh process. Any in-flight requests are dropped. Use this after deploying new code, changing `.env`, or upgrading dependencies, since a fresh process is the only way to guarantee the new code/venv is actually loaded.
* `systemctl reload` asks the running process to reload without dropping connections. Gunicorn's `ExecReload=/bin/kill -s HUP $MAINPID` (see [`gunicorn.service`](../config/systemd/gunicorn.service)) tells its workers to gracefully re-exec. This is fine for low-risk config-only changes, but it does **not** reliably pick up new packages installed into the virtual environment — use `restart` after a deploy.
* nginx supports the same distinction: `reload` re-reads its configuration with no dropped connections; `restart` fully re-executes the master process.

| Action | Command | Drops connections? | When to use |
|---|---|---|---|
| Restart Gunicorn | `sudo systemctl restart gunicorn` | Yes | After deploying new code, `.env` changes, or dependency updates |
| Reload Gunicorn | `sudo systemctl reload gunicorn` | No (graceful) | Minor config tweaks, zero-downtime |
| Restart nginx | `sudo systemctl restart nginx` | Briefly | Rare; e.g. an nginx binary upgrade |
| Reload nginx | `sudo systemctl reload nginx` | No | After editing the nginx site config |
| Restart PostgreSQL | `sudo systemctl restart postgresql` | Yes (drops DB connections) | After a `postgresql.conf` change that requires a restart |

## Start and stop

```bash
sudo systemctl start gunicorn
sudo systemctl stop gunicorn
```

## Enable and disable (boot behaviour)

The units are already enabled by [`scripts/deploy.sh`](../scripts/deploy.sh); use these commands to verify or change that:

```bash
sudo systemctl enable gunicorn.socket    # start on boot
sudo systemctl disable gunicorn.socket   # don't start on boot
sudo systemctl is-enabled gunicorn.socket
```

## Checking status

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql
```

If a service shows `failed` or `inactive`, see [troubleshooting.md](troubleshooting.md#service-status) for diagnosis.

# Viewing logs

To watch everything at once while you restart or deploy:

```bash
sudo journalctl -u gunicorn.service -u nginx.service --follow
```

For the full breakdown of log locations per service, filtering by time/priority, and reading logs to diagnose a specific error, see [troubleshooting.md](troubleshooting.md#finding-logs).

# Running management commands

All commands use [django-admin](https://docs.djangoproject.com/en/5.1/ref/django-admin/) via the `$django_admin` shell variable set up above.

## Built-in Django commands

| Command | Purpose | Example | Notes |
|---|---|---|---|
| `migrate` | Apply database schema migrations | `sudo $django_admin migrate` | Run after every deploy that includes model changes |
| `createsuperuser` | Create an admin account | `sudo $django_admin createsuperuser` | Interactive prompts for email/password |
| `changepassword` | Reset a user's password | `sudo $django_admin changepassword user@example.com` | See also [troubleshooting.md](troubleshooting.md#reset-a-users-password) |
| `collectstatic` | Gather static assets into `DJANGO_STATIC_ROOT` | `sudo $django_admin collectstatic --no-input` | Required after a frontend rebuild (`npm run build`) |
| `shell` | Interactive Python/Django shell | `sudo $django_admin shell` | See [troubleshooting.md](troubleshooting.md#interactive-django-shell) for query examples |
| `dbshell` | Interactive PostgreSQL shell | `sudo $django_admin dbshell` | See [deployment.md](deployment.md#database-administration) for schema commands |
| `check --deploy` | Run Django's production readiness checks | `sudo $django_admin check --deploy` | Also run automatically in `scripts/deploy.sh` |
| `loaddata` | Load fixtures | `sudo $python manage.py loaddata data/*.json` | Used for initial seed data |

## Custom SORT commands

| Command | App | Purpose | Example | Notes |
|---|---|---|---|---|
| `clear_orphaned_files` | home | Delete uploaded files no longer referenced by any `SurveyEvidenceFile`/`SurveyFile`, and any empty upload directories left behind | `sudo $django_admin clear_orphaned_files` | No arguments; safe to run repeatedly |
| `csv <survey_id>` | survey | Write one survey's responses as CSV to stdout | `sudo $django_admin csv 42 > survey_42.csv` | Positional integer survey PK |
| `excel <survey_id> [-o/--output PATH]` | survey | Write one survey's responses as an `.xlsx` workbook | `sudo $django_admin excel 42 --output /tmp/survey_42.xlsx` | Defaults to `survey_<id>_responses.xlsx` in the current directory if `--output` is omitted |
| `pdf <survey_id> [--output-dir DIR] [--base-url URL]` | survey | Render `/survey/<pk>/report` in headless Chromium and save it as a PDF | `sudo $django_admin pdf 42 --output-dir /tmp/reports --base-url https://sort-web-app.shef.ac.uk` | See prerequisites below. `--output-dir` defaults to `exports/reports`; `--base-url` defaults to `http://127.0.0.1:8000` and **must** be overridden in production |
| `usage` | survey | Write a usage report (organisations/surveys/responses counts) as CSV to stdout | `sudo $django_admin usage > usage_report.csv` | No arguments |
| `validate_responses` | survey | Validate every survey response against its survey's JSON Schema | `sudo $django_admin validate_responses` | No arguments; errors are printed to stderr and the command exits with status `1` if any are found, which makes it suitable for cron/monitoring |

### `pdf` command prerequisites

This command drives a real browser and needs an authenticated session, so it requires some one-off setup:

```bash
sudo $venv_dir/bin/pip install playwright
sudo $venv_dir/bin/playwright install chromium
```

It also needs at least one superuser account to exist (`sudo $django_admin createsuperuser`), since it authenticates by creating a session for the first superuser it finds.

## Scheduling recurring commands

`validate_responses` (exit-code aware) and `clear_orphaned_files` are both safe to run unattended and are good candidates for a cron job or systemd timer, e.g.:

```
0 3 * * * root cd /opt/sort && venv/bin/python manage.py clear_orphaned_files
```

No timer unit currently ships with this repo — set one up if you want this automated.

# Deploying an update to running code

To ship a code change to an already-provisioned server:

```bash
git pull
sudo $python -m pip install -r requirements.txt   # if dependencies changed
npm ci && npm run build                           # if frontend changed
sudo $django_admin migrate
sudo $django_admin collectstatic --no-input
sudo systemctl restart gunicorn
```

If anything goes wrong, see [troubleshooting.md](troubleshooting.md).

# See also

* [deployment.md](deployment.md) — initial server setup, systemd unit installation, TLS certificates, database creation
* [troubleshooting.md](troubleshooting.md) — diagnosing errors, log analysis by symptom, recovery procedures
* [data-management.md](data-management.md) — full-database export with `dumpdata`
