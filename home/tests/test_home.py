import django.test


class HomeTestCase(django.test.TestCase):

    def test_welcome_page(self):
        """
        Welcome page
        """
        self.client.get("/")
