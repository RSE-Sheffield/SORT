import django.test


class UserTestCase(django.test.TestCase):

    def test_profile_page(self):
        """
        Test the user profile page
        """
        self.client.get("/profile")
