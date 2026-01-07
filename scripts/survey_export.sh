#!/usr/bin/env bash
# Export a specific survey and its responses to JSON.
# This script requires the JSON processing tool jq.
# It also requires an active virtual environment with the Django libraries installed.
# Installation: sudo apt install jq
# Usage:
# source .venv/bin/activate
# ./survey_export.sh <survey_id> [output_file]

# Stop on errors
set -euo pipefail

# Django data export
# https://docs.djangoproject.com/en/5.2/ref/django-admin/#dumpdata

working_dir="$(mktemp --directory)"

# Check if survey ID was provided
if [ $# -eq 0 ]; then
  echo "Error: Survey ID required" >&2
  echo "Usage: $0 <survey_id> [output_file]" >&2
  exit 1
fi

# Export specific survey
primary_key="$1"

echo "Exporting survey PK $primary_key..."
python manage.py dumpdata survey.Survey --pks "$primary_key" --indent 2 --output "$working_dir/survey_$primary_key.json" --format json

# Export all responses for that survey (filter by survey FK)
echo "Exporting survey responses..."
python manage.py dumpdata survey.SurveyResponse --indent=2 --natural-primary | \
  jq --argjson pk "$primary_key" '[.[] | select(.fields.survey == $pk)]' > "$working_dir/survey_responses.json"

# Export invitations for that survey
echo "Exporting invitations..."
python manage.py dumpdata survey.Invitation --indent=2 --natural-primary | \
  jq --argjson pk "$primary_key" '[.[] | select(.fields.survey == $pk)]' > "$working_dir/invitations.json"

# Export evidence sections for that survey
echo "Exporting evidence sections..."
python manage.py dumpdata survey.SurveyEvidenceSection --indent=2 --natural-primary | \
  jq --argjson pk "$primary_key" '[.[] | select(.fields.survey == $pk)]' > "$working_dir/evidence_sections.json"

# Export evidence files (need to filter by evidence section PKs)
echo "Exporting evidence files..."
evidence_section_pks=$(jq '[.[].pk]' "$working_dir/evidence_sections.json")
python manage.py dumpdata survey.SurveyEvidenceFile --indent=2 --natural-primary | \
  jq --argjson pks "$evidence_section_pks" '[.[] | select([.fields.evidence_section] | inside($pks))]' > "$working_dir/evidence_files.json"

# Export improvement plan sections for that survey
echo "Exporting improvement plan sections..."
python manage.py dumpdata survey.SurveyImprovementPlanSection --indent=2 --natural-primary | \
  jq --argjson pk "$primary_key" '[.[] | select(.fields.survey == $pk)]' > "$working_dir/improvement_sections.json"

# Combine all exports
output_file="${2:-survey_${primary_key}_export.json}"
jq -s 'add' \
  "$working_dir/survey_$primary_key.json" \
  "$working_dir/survey_responses.json" \
  "$working_dir/invitations.json" \
  "$working_dir/evidence_sections.json" \
  "$working_dir/evidence_files.json" \
  "$working_dir/improvement_sections.json" \
  > "$output_file"

echo ""
echo "[OK] Export complete: $output_file"
echo ""

# List file paths
echo "File paths for SurveyEvidenceFile.file:"
jq -r '.[] | select(.model == "survey.surveyevidencefile") | .fields.file' "$output_file" | grep -v "^null$" || echo "  (none)"
echo ""

echo "To import:"
echo "  python manage.py loaddata \"$output_file\""
