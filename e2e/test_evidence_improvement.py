"""
Evidence gathering and improvement planning for a survey section.
"""

import tempfile

from django.test import override_settings

from e2e.base import PlaywrightTestCase, expect

STATEMENT = "Our research activity has grown this year."
OBJECTIVE = "Run a research awareness session for all staff"


class EvidenceImprovementTestCase(PlaywrightTestCase):
    def setUp(self):
        super().setUp()
        self.survey, self.user = self.create_survey()
        self.section_id = self.survey.evidence_sections.first().section_id
        self.login(self.user)

    def test_evidence_statement(self):
        page = self.page
        self.visit("survey_evidence_gathering", pk=self.survey.pk, section_id=self.section_id)

        page.locator(".sort-richtext-field [contenteditable=true]").fill(STATEMENT)
        with page.expect_navigation():
            page.get_by_role("button", name="Save statement").click()

        expect(page.locator(".sort-richtext-field [contenteditable=true]")).to_contain_text(STATEMENT)
        section = self.survey.evidence_sections.get(section_id=self.section_id)
        self.assertIn(STATEMENT, section.text)

    def test_evidence_file_upload(self):
        page = self.page
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.visit("survey_evidence_gathering", pk=self.survey.pk, section_id=self.section_id)
            page.locator("input[type=file][name=file]").set_input_files(
                {"name": "evidence.txt", "mimeType": "text/plain", "buffer": b"Some evidence"}
            )
            page.get_by_role("button", name="Upload file").click()
            expect(page.locator(".sort-file-browser")).to_contain_text("evidence.txt")

    def test_improvement_plan(self):
        page = self.page
        self.visit("survey_improvement_plan", pk=self.survey.pk, section_id=self.section_id)
        table = page.locator(".sort-smart-table")

        table.get_by_role("button", name="Add objective").click()
        row = table.locator("tbody tr").last
        row.locator("td textarea").nth(1).fill(OBJECTIVE)
        row.locator("input[type=text]").fill("Research lead")
        table.get_by_role("button", name="Save plan").click()

        page.wait_for_url(self.url("survey_improvement_plan", pk=self.survey.pk, section_id=self.section_id))
        expect(table.locator("tbody tr").last.locator("td textarea").nth(1)).to_have_value(OBJECTIVE)
        section = self.survey.improvement_sections.get(section_id=self.section_id)
        self.assertIn(OBJECTIVE, section.plan)
