"""
Research consent is optional (issue #729): participants who decline research use
must still be able to submit their response.
"""

from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from SORT.test.model_factory import SurveyFactory
from survey.models import RESEARCH_CONSENT_FIELD_NAME, Survey, SurveyResponse


def field_index(survey: Survey, name: str) -> int:
    fields = survey.sections[0]["fields"]
    return next(i for i, f in enumerate(fields) if f["name"] == name)


class ResearchConsentTestCase(TestCase):
    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.save()
        self.research_index = field_index(self.survey, RESEARCH_CONSENT_FIELD_NAME)
        self.consent_index = field_index(self.survey, "consent")

    def make_response(self, **consent_answers) -> SurveyResponse:
        answers = self.survey._generate_mock_response()
        for index, value in consent_answers.items():
            answers[0][int(index)] = value
        return SurveyResponse(survey=self.survey, answers=answers)

    def test_declining_research_consent_is_valid(self):
        response = self.make_response(**{str(self.research_index): []})
        response.clean()
        self.assertFalse(response.has_research_consent)

    def test_giving_research_consent(self):
        option = self.survey.sections[0]["fields"][self.research_index]["options"][0]
        response = self.make_response(**{str(self.research_index): [option]})
        response.clean()
        self.assertTrue(response.has_research_consent)

    def test_internal_consent_still_required(self):
        response = self.make_response(**{str(self.consent_index): []})
        with self.assertRaises(ValidationError):
            response.clean()

    def test_has_research_consent_with_missing_answers(self):
        response = SurveyResponse(survey=self.survey, answers=[])
        self.assertFalse(response.has_research_consent)


class MakeResearchConsentOptionalCommandTestCase(TestCase):
    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        # Simulate a survey created before research consent became optional
        self.index = field_index(self.survey, RESEARCH_CONSENT_FIELD_NAME)
        field = self.survey.survey_config["sections"][0]["fields"][self.index]
        self.template_description = field["description"]
        field["required"] = True
        field["description"] = "You must agree before proceeding."
        self.survey.save()

    def research_field(self) -> dict:
        self.survey.refresh_from_db()
        return self.survey.survey_config["sections"][0]["fields"][self.index]

    def test_dry_run_saves_nothing(self):
        out = StringIO()
        call_command("make_research_consent_optional", "--dry-run", stdout=out)
        self.assertTrue(self.research_field()["required"])
        self.assertIn(f"Would update survey {self.survey.pk}", out.getvalue())

    def test_makes_research_consent_optional(self):
        before = self.survey.survey_config
        call_command("make_research_consent_optional", stdout=StringIO())
        self.assertFalse(self.research_field()["required"])

        # Nothing else changed
        before["sections"][0]["fields"][self.index]["required"] = False
        before["sections"][0]["fields"][self.index][
            "description"
        ] = self.template_description
        self.assertEqual(self.survey.survey_config, before)

    def test_description_updated_to_template(self):
        call_command("make_research_consent_optional", stdout=StringIO())
        description = self.research_field()["description"]
        self.assertEqual(description, self.template_description)
        self.assertIn("This is optional", description)

    def test_dry_run_leaves_description(self):
        call_command("make_research_consent_optional", "--dry-run", stdout=StringIO())
        self.assertEqual(
            self.research_field()["description"], "You must agree before proceeding."
        )

    def test_internal_consent_left_required(self):
        call_command("make_research_consent_optional", stdout=StringIO())
        consent = self.survey.survey_config["sections"][0]["fields"][
            field_index(self.survey, "consent")
        ]
        self.assertTrue(consent["required"])

    def test_already_optional_is_skipped(self):
        call_command("make_research_consent_optional", stdout=StringIO())
        out = StringIO()
        call_command("make_research_consent_optional", stdout=out)
        self.assertIn("0 survey(s) updated, 1 skipped", out.getvalue())
