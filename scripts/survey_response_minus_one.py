#!/usr/bin/env python
"""Shift likert answers in SurveyResponse.answers from the 1-5 scale to 0-4.

Usage:
    python scripts/survey_response_minus_one.py <survey_pk>            # dry-run
    python scripts/survey_response_minus_one.py <survey_pk> --commit   # persist
"""

import argparse
import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SORT.settings")
django.setup()

from django.db import transaction  # noqa: E402
from survey.models import Survey  # noqa: E402

LIKERT_VALUES = {"1", "2", "3", "4", "5"}


def shift_answers(answers):
    """Return (new_answers, values_shifted). Raises ValueError if a '0' is seen."""
    new = list()
    shifted = 0
    for section in answers:
        new_section = list()
        for field in section:
            if isinstance(field, list):
                new_field = list()
                for v in field:
                    if v in LIKERT_VALUES:
                        new_field.append(str(int(v) - 1))
                        shifted += 1
                    elif v == "0":
                        raise ValueError(
                            f"unexpected '{v}' value in list-typed field - "
                            "survey may have been converted previously"
                        )
                    else:
                        new_field.append(v)
                new_section.append(new_field)
            else:
                new_section.append(field)
        new.append(new_section)
    return new, shifted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("survey_pk", type=int)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist changes. Without this flag the script runs read-only.",
    )
    args = parser.parse_args()

    survey = Survey.objects.get(pk=args.survey_pk)
    responses = list(survey.survey_response.all())

    total_shifted = 0
    modified = 0

    with transaction.atomic():
        for r in responses:
            try:
                new_answers, shifted = shift_answers(r.answers)
            except ValueError as e:
                raise ValueError(f"response pk={r.pk}: {e}") from e
            if shifted:
                r.answers = new_answers
                r.save(update_fields=["answers"])
                total_shifted += shifted
                modified += 1

        if not args.commit:
            transaction.set_rollback(True)
            print(
                f"dry-run: would modify {modified}/{len(responses)} responses "
                f"(shifted {total_shifted} values); re-run with --commit to persist."
            )
        else:
            print(
                f"committed: modified {modified}/{len(responses)} responses "
                f"(shifted {total_shifted} values)."
            )


if __name__ == "__main__":
    main()
