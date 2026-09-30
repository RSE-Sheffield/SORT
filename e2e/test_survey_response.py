"""
Survey capture: a manager shares an invitation link and a respondent fills in the survey.
"""

import re

from e2e.base import Page, PlaywrightTestCase, expect
from e2e.survey import COMMENT, INVALID_MESSAGE, LIKERT_SCORE, fill_pages, fill_section, get_fields
from survey.models import Invitation, SurveyResponse


class SurveyResponseTestCase(PlaywrightTestCase):
    def setUp(self):
        super().setUp()
        self.survey, self.user = self.create_survey()
        self.sections = self.survey.survey_config["sections"]

    def create_invite_link(self) -> str:
        """
        Generate an invitation link through the survey management page.
        """
        self.login(self.user)
        self.visit("survey", pk=self.survey.pk)
        self.page.get_by_role("button", name="Generate invitation").click()
        link = self.page.locator("#invitation_link")
        expect(link).to_have_value(re.compile(r"/survey_response/"))
        return link.input_value()

    def open_survey(self) -> Page:
        token = Invitation.objects.get(survey=self.survey, used=False).token
        page = self.new_anonymous_page()
        self.visit("survey_response", page=page, token=token)
        return page

    def test_complete_survey(self):
        link = self.create_invite_link()

        # The respondent is not logged in
        page = self.new_anonymous_page()
        page.goto(link)

        fill_pages(page, self.sections[:-1])
        fill_section(page, self.sections[-1])
        page.get_by_role("button", name="Submit").click()

        expect(page.get_by_role("heading", name="Survey Completed!")).to_be_visible()
        self.assertEqual(page.url, self.url("completion_page"))

        # Check the answers were saved
        response = SurveyResponse.objects.get(survey=self.survey)
        answers = response.answers
        self.assertEqual(len(answers), len(self.sections))
        for section, section_answers in zip(self.sections, answers):
            for config, answer in zip(section["fields"], section_answers):
                if config["type"] == "likert":
                    self.assertEqual(answer, [LIKERT_SCORE] * len(config["sublabels"]))
                elif config["type"] == "textarea":
                    self.assertEqual(answer, COMMENT)

    def test_required_fields(self):
        """
        The respondent can't continue until the required questions are answered.
        """
        self.create_invite_link()
        page = self.open_survey()
        first, second = self.sections[0], self.sections[1]

        page.get_by_role("button", name="Next >").click()
        expect(page.get_by_text(INVALID_MESSAGE)).to_be_visible()
        expect(page.get_by_role("heading", name=first["title"], exact=True)).to_be_visible()

        fill_section(page, first)
        page.get_by_role("button", name="Next >").click()
        expect(page.get_by_role("heading", name=second["title"], exact=True)).to_be_visible()
        expect(page.get_by_text(INVALID_MESSAGE)).to_be_hidden()

        # A partially answered likert question is still invalid
        likert = get_fields(page).first
        likert.locator("tbody tr").first.get_by_label(f"Score {LIKERT_SCORE}", exact=True).check()
        page.get_by_role("button", name="Next >").click()
        expect(page.get_by_text(INVALID_MESSAGE)).to_be_visible()
        # The second statement hasn't been answered
        expect(likert.locator("tbody tr").nth(1).get_by_text("A value must be selected")).to_be_visible()

    def test_previous_page_keeps_answers(self):
        self.create_invite_link()
        page = self.open_survey()
        first, second = self.sections[0], self.sections[1]
        previous = page.get_by_role("button", name="< Previous")

        expect(previous).to_be_disabled()
        fill_section(page, first)
        page.get_by_role("button", name="Next >").click()
        fill_section(page, second)

        previous.click()
        expect(page.get_by_role("heading", name=first["title"], exact=True)).to_be_visible()
        for option in page.locator(".sort-survey-response input[type=checkbox]").all():
            expect(option).to_be_checked()

        page.get_by_role("button", name="Next >").click()
        rows = get_fields(page).first.locator("tbody tr")
        for row in rows.all():
            expect(row.get_by_label(f"Score {LIKERT_SCORE}", exact=True)).to_be_checked()

        # Nothing is saved until the survey is submitted
        self.assertFalse(SurveyResponse.objects.filter(survey=self.survey).exists())

    def test_invalid_link(self):
        page = self.new_anonymous_page()
        page.goto(self.url("survey_response", token="not-a-real-token"))
        expect(page.get_by_role("heading", name="Your survey link is invalid")).to_be_visible()

    def test_inactive_survey(self):
        self.create_invite_link()
        self.survey.is_active = False
        self.survey.save()
        page = self.open_survey()
        expect(page.get_by_role("heading", name="Survey inactive")).to_be_visible()
