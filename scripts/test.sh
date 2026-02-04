#!/bin/bash
set -e

# Backend tests (Django)
python manage.py test home/tests --parallel=auto --failfast
python manage.py test survey/tests --parallel=auto --failfast
