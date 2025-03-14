from http import HTTPStatus
import django.test
import django.urls
from django.contrib.auth import get_user_model
from constants import PASSWORD

User = get_user_model()


class UserTestCase(django.test.TestCase):
    def setUp(self):
        self.user = User.objects.create_user('John', 'Smith', 'john.smith@sheffield.ac.uk', PASSWORD)

    def login(self):
        self.assertTrue(self.client.login(username=self.user.email, password=PASSWORD))

    def test_profile_page(self):
        """
        Test the user profile page
        """
        self.login()
        response = self.client.get(django.urls.reverse('profile'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_get(self):
        response = self.client.get(django.urls.reverse('login'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_post(self):
        response = self.client.post(
            django.urls.reverse('login'),
            {"username": self.user.get_username(), "password": self.user.password}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout(self):
        self.login()
        response = self.client.post(django.urls.reverse('logout'))
        # Expect to be redirected
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
