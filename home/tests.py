import django.test
from django.test import TestCase


class HomeTestCase(TestCase):
    def setUp(self):
        self.client = django.test.Client()

    def test_home_view(self):
        """
        Welcome page
        """
        self.client.get('/')
