from http import HTTPStatus

import SORT.test.test_case
from django.template import Context, Template
from django.test import RequestFactory
from SORT.test.model_factory import OrganisationFactory, ProjectFactory, SurveyFactory, UserFactory
from SORT.test.model_factory.user.constants import PASSWORD


class ConsoleSortingTests(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)
        self.assertTrue(self.client.login(username=self.staff_user.email, password=PASSWORD))

    def names(self, url, context_key, attr="name"):
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        return [getattr(o, attr) for o in response.context[context_key]]

    def test_organisations_sort_by_name_both_directions(self):
        for name in ("Bravo", "Alpha", "Charlie"):
            OrganisationFactory(name=name)
        asc = self.names("/console/organisations/?sort=name&dir=asc", "organisations")
        desc = self.names("/console/organisations/?sort=name&dir=desc", "organisations")
        self.assertEqual(asc, sorted(asc))
        self.assertEqual(desc, sorted(desc, reverse=True))

    def test_organisations_sort_by_annotated_count(self):
        big = OrganisationFactory(name="Big")
        OrganisationFactory(name="Small")
        ProjectFactory(organisation=big)
        ProjectFactory(organisation=big)
        rows = self.names("/console/organisations/?sort=projects&dir=desc", "organisations")
        self.assertEqual(rows[0], "Big")

    def test_invalid_sort_falls_back_to_default(self):
        OrganisationFactory(name="Alpha")
        response = self.client.get("/console/organisations/?sort=__class__&dir=sideways")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["sort"], "name")
        self.assertEqual(response.context["dir"], "asc")

    def test_users_sort_by_email_descending(self):
        emails = self.names("/console/users/?sort=email&dir=desc", "users", "email")
        self.assertEqual(emails, sorted(emails, reverse=True))

    def test_users_sort_kept_by_status_filter_links(self):
        response = self.client.get("/console/users/?sort=email&dir=desc")
        self.assertContains(response, "?status=all&sort=email&dir=desc")

    def test_projects_sort_by_survey_count(self):
        busy = ProjectFactory(name="Busy")
        ProjectFactory(name="Quiet")
        SurveyFactory(project=busy)
        SurveyFactory(project=busy)
        rows = self.names("/console/projects/?sort=surveys&dir=desc", "projects")
        self.assertEqual(rows[0], "Busy")

    def test_surveys_sort_by_name(self):
        project = ProjectFactory()
        for name in ("Zed", "Abe"):
            SurveyFactory(project=project, name=name)
        rows = self.names("/console/surveys/?sort=name&dir=asc", "surveys")
        self.assertEqual(rows, sorted(rows))

    def test_surveys_default_is_newest_first(self):
        response = self.client.get("/console/surveys/")
        self.assertEqual((response.context["sort"], response.context["dir"]), ("created", "desc"))

    def test_data_protection_log_sort_and_page_preserved(self):
        response = self.client.get("/console/data-protection/?sort=event&dir=asc&page=1")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["sort"], "event")
        self.assertIn("sort=event", response.context["filter_qs"])


class SortHeaderTagTests(SORT.test.test_case.ViewTestCase):
    def render(self, query, sort="name", direction="asc"):
        request = RequestFactory().get("/console/users/" + query)
        template = Template('{% load console_tags %}{% sort_header "name" "Name" %}')
        return template.render(Context({"request": request, "sort": sort, "dir": direction}))

    def test_active_ascending_column_links_to_descending(self):
        html = self.render("?sort=name&dir=asc")
        self.assertIn('aria-sort="ascending"', html)
        self.assertIn("dir=desc", html)

    def test_inactive_column_links_to_ascending(self):
        html = self.render("", sort="email")
        self.assertIn('aria-sort="none"', html)
        self.assertIn("dir=asc", html)

    def test_other_params_kept_and_page_dropped(self):
        html = self.render("?status=all&page=3")
        self.assertIn("status=all", html)
        self.assertNotIn("page=", html)
