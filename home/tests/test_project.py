import django.test


class ProjectTestCase(django.test.TestCase):

    def test_projects_page(self):
        """
        Test the profiles list page.
        """
        self.client.get("/projects")
