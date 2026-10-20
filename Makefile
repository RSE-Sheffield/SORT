# Custom Django Development Makefile
# This Makefile contains common Django management commands for easier development

# Variables
PYTHON = .venv/bin/python
MANAGE = $(PYTHON) manage.py
PROJECT_NAME = SORT

# Development server
runserver:
	$(MANAGE) runserver

# Database operations
migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

# System checks
check:
	$(MANAGE) check --fail-level WARNING
	$(MANAGE) makemigrations --check --dry-run

# User management
superuser:
	$(MANAGE) createsuperuser

# Static files
static:
	$(MANAGE) collectstatic --noinput

# Development tools
shell:
	$(MANAGE) shell

test:
	$(MANAGE) test --parallel=auto --failfast --exclude-tag=e2e
	npm test

# End-to-end browser tests (requires: playwright install chromium)
e2e:
	npm run build
	$(MANAGE) test e2e --tag=e2e

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Dependencies
requirements:
	pip install -r requirements.txt

# Code quality - only check project source files
lint:
	flake8

# Security scans: Bandit (code) and pip-audit (dependencies)
security:
	.venv/bin/bandit -r . -c pyproject.toml --severity-level medium
	.venv/bin/pip-audit -r requirements.txt

format:
	black $(PROJECT_NAME) --exclude="migrations|settings.py"

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Mark these targets as always needing to run (not files)
.PHONY: help runserver migrations migrate check superuser static shell test e2e clean requirements lint security
