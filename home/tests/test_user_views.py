"""
Test user profile and authentication views
"""

from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory import UserFactory
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

    def test_logout(self):
        # Expect to be redirected
        self.post("logout", expected_status_code=HTTPStatus.FOUND, login=True)

    def test_login_suspended_user_shows_suspension_message(self):
        """A suspended user with correct credentials sees a clear message."""
        suspended = UserFactory(is_active=False)
        response = self.post(
            "login",
            data=dict(username=suspended.email, password=PASSWORD),
            login=False,
        )
        self.assertContains(response, "suspended")
        # They are not authenticated.
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_password_shows_generic_message(self):
        """An incorrect password shows the generic error, not the suspension one."""
        response = self.post(
            "login",
            data=dict(username=self.user.email, password="not-the-password"),
            login=False,
        )
        self.assertContains(response, "Invalid email or password")
