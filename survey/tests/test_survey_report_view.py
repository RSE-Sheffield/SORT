"""
Tests for the survey report page, which renders the data analysis of a survey's
responses.
"""

from http import HTTPStatus

import SORT.test.model_factory
import SORT.test.test_case
from survey.models import SurveyResponse


class SurveyReportViewTestCase(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.survey = SORT.test.model_factory.SurveyFactory()
        self.organisation = self.survey.project.organisation
        self.user = self.organisation.members.first()
        self.survey.initialise()
        self.survey.save()

    def test_survey_report_get_unauthorised(self):
        # Redirect to the login page
        self.get(
            "survey_report",
            expected_status_code=HTTPStatus.FOUND,
            login=False,
            pk=self.survey.pk,
        )

    def test_survey_report_without_responses(self):
        response = self.get("survey_report", pk=self.survey.pk)

        self.assertEqual(response.context["response_count"], 0)
        self.assertEqual(response.context["invalid_response_count"], 0)
        self.assertNotContains(response, "Some responses could not be included in full")

    def test_survey_report_with_valid_responses(self):
        self.survey.generate_mock_responses(num_responses=3)

        response = self.get("survey_report", pk=self.survey.pk)

        self.assertEqual(response.context["response_count"], 3)
        self.assertEqual(response.context["invalid_response_count"], 0)
        self.assertEqual(len(response.context["responses"]), 3)
        self.assertNotContains(response, "Some responses could not be included in full")

    def test_survey_report_warns_about_responses_that_do_not_match_the_survey(self):
        """
        Answers recorded before a question was added to the survey configuration hold
        fewer values than there are fields. The report must still render, and must say
        that the figures are incomplete.
        """
        self.survey.generate_mock_responses(num_responses=2)
        # Bypass full_clean(): this is the shape of data already in the database, which
        # cannot be created through the normal submission path any more.
        answers = self.survey._generate_mock_response()
        del answers[0][-1]
        SurveyResponse.objects.create(survey=self.survey, answers=answers)

        response = self.get("survey_report", pk=self.survey.pk)

        self.assertEqual(response.context["response_count"], 3)
        self.assertEqual(response.context["invalid_response_count"], 1)
        # The malformed answers are still sent to the browser, which skips what it
        # cannot use, so the other answers in that response are not lost.
        self.assertEqual(len(response.context["responses"]), 3)
        self.assertContains(response, "Some responses could not be included in full")

    def test_survey_report_with_a_response_missing_a_whole_section(self):
        self.survey.generate_mock_responses(num_responses=1)
        answers = self.survey._generate_mock_response()
        del answers[-1]
        SurveyResponse.objects.create(survey=self.survey, answers=answers)

        response = self.get("survey_report", pk=self.survey.pk)

        self.assertEqual(response.context["invalid_response_count"], 1)
        self.assertContains(response, "Some responses could not be included in full")
