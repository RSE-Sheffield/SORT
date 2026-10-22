"""
Load each key page in a real browser and check it works without Python or JavaScript errors.
"""

import SORT.test.model_factory
from e2e.base import PlaywrightTestCase, expect
from survey.services import survey_service

# Pages that anyone can view without logging in
PUBLIC_PAGES = (
    "landing",
    "login",
    "help",
    "faq",
    "troubleshooting",
    "eula",
    "privacy",
    "participant_information",
    "completion_page",
    "survey_link_invalid",
    "survey_response_inactive",
)


class PublicPagesTestCase(PlaywrightTestCase):
    def test_public_pages(self):
        for name in PUBLIC_PAGES:
            with self.subTest(page=name):
                self.visit(name)
                expect(self.page.locator("body")).not_to_be_empty()


class ManagerPagesTestCase(PlaywrightTestCase):
    """
    Pages used by an organisation administrator to manage a survey that has responses.
    """

    def setUp(self):
        super().setUp()
        self.survey, self.user = self.create_survey()
        # Mock responses are needed to draw the charts and reports
        survey_service.generate_mock_responses(SORT.test.model_factory.SuperUserFactory(), self.survey, 5)
        self.section_id = self.survey.evidence_sections.first().section_id
        self.login(self.user)

    def assert_mounted(self, selector: str):
        """
        Check that a Svelte component rendered some content into its mount point.
        """
        # Some components (e.g. an empty file list) render nothing visible, so just check for elements
        expect(self.page.locator(selector).first.locator("> *")).not_to_have_count(0)

    def test_home_pages(self):
        project = self.survey.project
        for name, kwargs in (
            ("dashboard", {}),
            ("profile", {}),
            ("myorganisation", {}),
            ("members", {}),
            ("project", {"project_id": project.pk}),
            ("survey", {"pk": self.survey.pk}),
        ):
            with self.subTest(page=name):
                self.visit(name, **kwargs)
                expect(self.page.locator("h1, h2").first).to_be_visible()

    def test_survey_pages(self):
        """
        Pages that mount Svelte components: check each component renders.
        """
        pk = self.survey.pk
        for name, kwargs, selectors in (
            ("survey_response_data", {"pk": pk}, [".sort-response-viewer"]),
            (
                "survey_evidence_gathering",
                {"pk": pk, "section_id": self.section_id},
                [".sort-response-section-viewer", ".sort-richtext-field", ".sort-file-browser"],
            ),
            (
                "survey_improvement_plan",
                {"pk": pk, "section_id": self.section_id},
                [".sort-response-section-viewer", ".sort-richtext-field", ".sort-smart-table"],
            ),
            ("survey_report", {"pk": pk}, [".sort-report-app"]),
        ):
            with self.subTest(page=name):
                self.visit(name, **kwargs)
                for selector in selectors:
                    self.assert_mounted(selector)

    def test_survey_configure(self):
        # Configuration is locked once a survey has responses, so use a fresh survey
        survey, user = self.create_survey()
        self.login(user)
        self.visit("survey_configure", pk=survey.pk)
        self.assert_mounted(".sort-consent-demography-config")
