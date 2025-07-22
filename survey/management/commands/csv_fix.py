import csv
import logging
import sys

from django.core.management import BaseCommand

from survey.models import Survey, SurveyResponse

# TODO delete this file

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Survey CSV export

    This is a bodge to export malformed data pre-August 2025.

    This will not be accurate for all possible input data, but is particular to how the data happens to look at the
    time of writing.
    """

    help = "Export a survey response to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("survey_id", type=int, help="Survey primary key (integer)")

    @classmethod
    def build_row(
        cls, sections: list[dict], survey_response: SurveyResponse
    ) -> dict[str, str]:
        """
        Map a set of survey response answers to a row of data (key-value pairs).
        """
        # Generate field-answer mapping on a per-section basis because this helps us to fix the malformed data
        for section, answers in zip(sections, survey_response.answers):
            yield from cls.map_answers(section, answers)

    @classmethod
    def map_answers(cls, section: dict, section_answers: list[list[str]]):
        """
        Map section fields to the answers in SurveyResponse.answers.
        """
        logger.debug("SECTION %s", section["title"])
        for field_index, field in enumerate(section["fields"]):
            logger.debug("FIELD '%s'", field["label"])

            # *** This is the hack. ***
            # If an answer is missing, fill in the undefined value with a missing (null) value.
            try:
                field_answers = section_answers[field_index]
            except IndexError:
                yield field["label"], None
                continue

            # Likert fields
            if field["sublabels"]:
                yield from zip(field["sublabels"], field_answers)
            else:
                yield field["label"], field_answers

    def handle(self, *args, **options):
        survey = Survey.objects.get(pk=options["survey_id"])

        headers = survey.fields

        # CSV export
        writer = csv.DictWriter(
            sys.stdout, fieldnames=headers, lineterminator="\n", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()

        # Iterate over survey response submissions
        for survey_response in survey.survey_response.all():
            logger.debug(survey_response)
            row = dict(self.build_row(survey.sections, survey_response))
            writer.writerow(row)
