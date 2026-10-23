"""
Logging in through the login form.
"""

import SORT.test.model_factory
from e2e.base import PlaywrightTestCase, expect
from SORT.test.model_factory.user.constants import PASSWORD


class LoginTestCase(PlaywrightTestCase):
    def setUp(self):
        super().setUp()
        self.user = SORT.test.model_factory.UserFactory()

    def submit_login(self, password: str):
        self.visit("login")
        self.page.get_by_label("Email").fill(self.user.email)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()

    def test_login(self):
        self.submit_login(PASSWORD)
        self.page.wait_for_url(self.url("dashboard") + "**")

    def test_login_wrong_password(self):
        self.submit_login("wrong-password")
        expect(self.page.get_by_text("Invalid email or password.")).to_be_visible()
        self.assertTrue(self.page.url.startswith(self.url("login")))

    def test_login_required(self):
        self.page.goto(self.url("dashboard"))
        self.assertTrue(self.page.url.startswith(self.url("login")))
