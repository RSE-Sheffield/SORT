"""
Test user profile and authentication views
"""

from http import HTTPStatus

import django.test
import django.urls

import SORT.test.test_case


class UserViewTestCase(SORT.test.test_case.ViewTestCase):

    def test_profile_page(self):
        """
        Test the user profile page
        """
        self.get("profile")

    def test_login_get(self):
        response = self.client.get(django.urls.reverse("login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_post(self):
        response = self.client.post(
            django.urls.reverse("login"),
            {"username": self.user.get_username(), "password": self.user.password},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout(self):
        self.login()
        response = self.client.post(django.urls.reverse("logout"))
        # Expect to be redirected
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
