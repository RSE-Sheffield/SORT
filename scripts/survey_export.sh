#!/usr/bin/env bash
# Export a specific survey and its responses to JSON
# Usage: ./survey_export.sh <survey_id> [output_file]

set -euo pipefail

# Django data export
# https://docs.djangoproject.com/en/5.2/ref/django-admin/#dumpdata

# Export entire database
# python manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin.logentry --exclude sessions.session --indent 2 --output "sort-dumpdata.json"

working_dir="$(mktemp --directory)"

# Export specific survey
primary_key=60
python manage.py dumpdata survey.Survey --pks "$primary_key" --indent 2 --output "$working_dir/survey_$primary_key.json" --format json

# Export all responses for that survey (filter by survey FK)
python manage.py dumpdata survey.SurveyResponse --indent=2 --natural-primary | \
  jq --argjson pk "$primary_key" '[.[] | select(.fields.survey == $pk)]' > "$working_dir/survey_2_survey_responses.json"

# Combine them
jq -s 'add' "$working_dir/survey_2.json" "$working_dir/survey_2_survey_responses.json" > "$working_dir/survey_2_with_responses.json"

echo "Wrote $working_dir/survey_2_with_responses.json"

# To import:
# python manage.py loaddata "$working_dir/survey_2_with_responses.json"
