from django.test import SimpleTestCase, override_settings

from home.templatetags import vite_integration


@override_settings(DEBUG=True, VITE_BASE_URL="http://localhost:5173")
class ViteDebugTagsTests(SimpleTestCase):
    def test_vite_client_points_at_dev_server(self):
        html = vite_integration.vite_client()
        self.assertIn("http://localhost:5173/@vite/client", html)

    def test_vite_asset_points_at_dev_server(self):
        html = vite_integration.vite_asset("src/main.js")
        self.assertIn("http://localhost:5173/src/main.js", html)


@override_settings(DEBUG=False)
class ViteProductionTagsTests(SimpleTestCase):
    def test_vite_client_empty_outside_debug(self):
        self.assertEqual(vite_integration.vite_client(), "")
