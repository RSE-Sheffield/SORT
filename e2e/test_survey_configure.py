"""
Survey configuration: a manager customises the demographic questions.
"""

from e2e.base import PlaywrightTestCase, expect
from e2e.survey import fill_pages
from survey.models import Invitation

NEW_QUESTION = "Which team do you work in?"


class SurveyConfigureTestCase(PlaywrightTestCase):
    def setUp(self):
        super().setUp()
        self.survey, self.user = self.create_survey()
        self.login(self.user)

    def test_add_demographic_question(self):
        page = self.page
        self.visit("survey_configure", pk=self.survey.pk)

        demography = page.locator(".card").filter(
            has=page.get_by_role("heading", name="Configure your demographic page")
        )
        fields = demography.locator("a.sort-form-component")
        field_count = fields.count()

        demography.get_by_role("button", name="Add field").click()
        expect(fields).to_have_count(field_count + 1)
        fields.last.click()
        demography.get_by_label("Question label").fill(NEW_QUESTION)
        demography.get_by_role("button", name="close").click()
        expect(fields.last).to_contain_text(NEW_QUESTION)

        page.get_by_role("button", name="Save").click()
        expect(page.get_by_text("Survey configuration saved")).to_be_visible()
        self.assertEqual(page.url, self.url("survey", pk=self.survey.pk))

        # The new question is saved at the end of the demographic section
        self.survey.refresh_from_db()
        sections = self.survey.survey_config["sections"]
        self.assertEqual(sections[-1]["fields"][-1]["label"], NEW_QUESTION)

        # Respondents see the new question on the final page
        page.get_by_role("button", name="Generate invitation").click()
        token = Invitation.objects.get(survey=self.survey, used=False).token
        respondent = self.new_anonymous_page()
        self.visit("survey_response", page=respondent, token=token)
        fill_pages(respondent, sections[:-1])
        expect(respondent.get_by_label(NEW_QUESTION)).to_be_visible()
