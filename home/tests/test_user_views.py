"""
Test user profile and authentication views
"""

from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory.user.constants import PASSWORD


class UserViewTestCase(SORT.test.test_case.ViewTestCase):

    def test_profile_page(self):
        """
        Test the user profile page
        """
        self.get("profile", login=True)

    def test_login_get(self):
        self.get("login", login=False)

    def test_login_post(self):
        self.post(
            "login",
            data=dict(
                username=self.user.get_username(),
                password=self.user.password,
            ),
            login=False,
        )

    def test_login_post_case_insensitive_email(self):
        """
        Login should succeed even if the email is submitted with different
        case than stored (issue #667).
        """
        self.assertTrue(
            self.client.login(
                username=self.user.email.upper(),
                password=PASSWORD,
            ),
            "Authentication with a differently-cased email should succeed",
        )

    def test_logout(self):
        # Expect to be redirected
        self.post("logout", expected_status_code=HTTPStatus.FOUND, login=True)
