#!/usr/bin/env bash

# Script to reduce Likert response values by 1 in Django survey export JSON
# Usage: ./scripts/survey_response_minus_one.sh <input_file.json>
# Example:
# ./scripts/survey_response_minus_one.sh [input_file] > [output_file]

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <input_json_file>" >&2
    exit 1
fi

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found" >&2
    exit 1
fi

# Use jq to process the JSON
# For each object where model is "survey.surveyresponse",
# modify the Likert responses in fields.answers[1][0] through fields.answers[5][0]
# by reducing each string number by 1
jq 'map(
  if .model == "survey.surveyresponse" then
    .fields.answers |= (
      # Process indices 1 through 5 (the Likert sections)
      .[1][0] = (.[1][0] | map((. | tonumber - 1) | tostring)) |
      .[2][0] = (.[2][0] | map((. | tonumber - 1) | tostring)) |
      .[3][0] = (.[3][0] | map((. | tonumber - 1) | tostring)) |
      .[4][0] = (.[4][0] | map((. | tonumber - 1) | tostring)) |
      .[5][0] = (.[5][0] | map((. | tonumber - 1) | tostring))
    )
  else
    .
  end
)' "$INPUT_FILE"
