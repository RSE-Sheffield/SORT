from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory import UserFactory
from SORT.test.model_factory.user.constants import PASSWORD


class ConsoleViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)

    def login_staff(self):
        self.assertTrue(
            self.client.login(username=self.staff_user.email, password=PASSWORD),
            "Staff authentication failed",
        )

    def test_console_dashboard_accessible_to_staff(self):
        """Staff users can access the console dashboard."""
        self.login_staff()
        response = self.client.get("/console/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_dashboard_redirects_anonymous(self):
        """Anonymous users are redirected away from the console dashboard."""
        response = self.client.get("/console/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_dashboard_forbidden_for_regular_users(self):
        """Regular (non-staff) users cannot access the console dashboard."""
        self.login()
        response = self.client.get("/console/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_organisations_accessible_to_staff(self):
        """Staff users can access the organisations list."""
        self.login_staff()
        response = self.client.get("/console/organisations/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_organisations_redirects_anonymous(self):
        """Anonymous users are redirected away from the organisations list."""
        response = self.client.get("/console/organisations/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_organisations_forbidden_for_regular_users(self):
        """Regular users cannot access the organisations list."""
        self.login()
        response = self.client.get("/console/organisations/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_users_accessible_to_staff(self):
        """Staff users can access the users list."""
        self.login_staff()
        response = self.client.get("/console/users/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_users_redirects_anonymous(self):
        """Anonymous users are redirected away from the users list."""
        response = self.client.get("/console/users/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_users_forbidden_for_regular_users(self):
        """Regular users cannot access the users list."""
        self.login()
        response = self.client.get("/console/users/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_surveys_accessible_to_staff(self):
        """Staff users can access the surveys list."""
        self.login_staff()
        response = self.client.get("/console/surveys/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_surveys_redirects_anonymous(self):
        """Anonymous users are redirected away from the surveys list."""
        response = self.client.get("/console/surveys/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_surveys_forbidden_for_regular_users(self):
        """Regular users cannot access the surveys list."""
        self.login()
        response = self.client.get("/console/surveys/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
