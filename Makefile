# Custom Django Development Makefile
# This Makefile contains common Django management commands for easier development

# Variables
PYTHON = python
MANAGE = $(PYTHON) manage.py
PROJECT_NAME = SORT

# Help command to list all available commands
help:
	@echo "Available commands:"
	@echo "  make runserver        - Start Django development server"
	@echo "  make migrations       - Create new database migrations"
	@echo "  make migrate          - Apply database migrations"
	@echo "  make check            - Run Django system checks (including migration check)"
	@echo "  make superuser       - Create a superuser account"
	@echo "  make static          - Collect static files"
	@echo "  make shell           - Open Django shell"
	@echo "  make test            - Run tests"
	@echo "  make clean           - Remove Python compiled files"
	@echo "  make requirements    - Install Python dependencies"
	@echo "  make lint            - Run code linting on project files"

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
	$(MANAGE) test

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Dependencies
requirements:
	pip install -r requirements.txt

# Code quality - only check project source files
lint:
	flake8 $(PROJECT_NAME) --exclude=migrations,settings.py
	black $(PROJECT_NAME) --exclude="migrations|settings.py"

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Mark these targets as always needing to run (not files)
.PHONY: help runserver migrations migrate check superuser static shell test clean requirements lint