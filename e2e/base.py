"""
Base class for end-to-end browser tests.

These tests run the real Django app (via a live test server) together with the
built Svelte bundle in a headless Chromium browser using Playwright.

Each test fails if the browser reports an uncaught JavaScript exception, a
console error, or any HTTP 5xx response.
"""

import contextlib
import os
import re
import unittest
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings, tag
from django.urls import reverse

import SORT.test.model_factory
from home.models import User
from survey.models import Survey
from survey.services import survey_service

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Locator, Page, expect, sync_playwright
except ImportError:  # pragma: no cover
    # The tests are skipped (see below), but the modules must still be importable for test discovery
    Locator = Page = PlaywrightError = expect = sync_playwright = None

# The Vite build output that the templates load when DEBUG is off
VITE_MANIFEST = Path(settings.BASE_DIR) / "static" / settings.VITE_MANIFEST_FILE_PATH

# Screenshots of failed tests are saved here
RESULTS_DIR = Path(settings.BASE_DIR) / "test-results"

# Desktop-sized viewport so that the likert tables are shown (not the mobile layout)
VIEWPORT = {"width": 1280, "height": 900}

# Milliseconds to wait for an element or navigation before failing
TIMEOUT_MS = 10_000


def _skip_reason() -> str | None:
    if sync_playwright is None:
        return "Playwright is not installed (pip install -r requirements-dev.txt)"
    if not VITE_MANIFEST.exists():
        return f"Front-end assets not built: {VITE_MANIFEST} is missing (run: npm run build)"
    return None


@tag("e2e")
@override_settings(SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class PlaywrightTestCase(StaticLiveServerTestCase):
    """
    A live-server test case with a Playwright browser page available as ``self.page``.
    """

    # Regular expressions for console error messages that are safe to ignore
    allowed_console_errors: list[str] = []

    @classmethod
    def setUpClass(cls):
        reason = _skip_reason()
        if reason:
            raise unittest.SkipTest(reason)
        # Playwright's sync API runs an asyncio event loop in the main thread, which
        # makes Django refuse synchronous ORM calls unless this is set.
        # Register cleanups straight after acquiring each resource, as tearDownClass
        # is not called if setUpClass raises (e.g. Chromium is not installed).
        cls.addClassCleanup(cls._restore_async_unsafe, os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE"))
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        try:
            cls.browser = cls.playwright.chromium.launch(
                headless=not os.getenv("E2E_HEADED"),
            )
        except PlaywrightError as exc:
            raise unittest.SkipTest(f"Chromium could not be launched (run: playwright install chromium): {exc}")
        cls.addClassCleanup(cls.browser.close)

    @staticmethod
    def _restore_async_unsafe(previous):
        if previous is None:
            os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = previous

    def setUp(self):
        super().setUp()
        self.errors: list[str] = []
        self.pages = []
        self.context = self.browser.new_context(viewport=VIEWPORT)
        self.context.set_default_timeout(TIMEOUT_MS)
        self.page = self.new_page()

    def tearDown(self):
        if self.errors:
            self.save_screenshots()
        self.context.close()
        super().tearDown()
        self.assertEqual(self.errors, [], "Errors were reported by the browser or server")

    def new_page(self, context=None):
        """
        Open a new browser tab that records JavaScript and server errors.
        """
        page = (context or self.context).new_page()
        self.pages.append(page)
        page.on("pageerror", lambda exc: self.errors.append(f"JavaScript error on {page.url}: {exc}"))
        page.on("console", self._on_console)
        page.on("response", self._on_response)
        return page

    def new_anonymous_page(self):
        """
        Open a page in a separate browser context, with no logged-in session.
        """
        context = self.browser.new_context(viewport=VIEWPORT)
        context.set_default_timeout(TIMEOUT_MS)
        self.addCleanup(context.close)
        return self.new_page(context)

    def _on_console(self, message):
        if message.type != "error":
            return
        if any(re.search(pattern, message.text) for pattern in self.allowed_console_errors):
            return
        self.errors.append(f"Console error on {message.location.get('url')}: {message.text}")

    def _on_response(self, response):
        if response.status >= 500:
            self.errors.append(f"HTTP {response.status} from {response.request.method} {response.url}")

    def save_screenshots(self, label: str = ""):
        """
        Save a screenshot of every open page, to help debug failures.
        """
        RESULTS_DIR.mkdir(exist_ok=True)
        for i, page in enumerate(self.pages):
            if not page.is_closed():
                page.screenshot(path=RESULTS_DIR / f"{self.id()}{label}-{i}.png", full_page=True)

    def _callTestMethod(self, method):
        # Take screenshots at the point of failure, while the pages are still open
        # (Call the method directly: unittest hides traceback frames below its own code)
        try:
            method()
        except unittest.SkipTest:
            raise
        except Exception:
            self.save_screenshots()
            raise

    @contextlib.contextmanager
    def subTest(self, msg=unittest.case._subtest_msg_sentinel, **params):
        with super().subTest(msg, **params):
            try:
                yield
            except unittest.SkipTest:
                raise
            except Exception:
                self.save_screenshots("-" + "-".join(f"{k}={v}" for k, v in params.items()))
                raise

    # Helpers

    def url(self, name: str, **kwargs) -> str:
        return self.live_server_url + reverse(name, kwargs=kwargs or None)

    def visit(self, name: str, page=None, **kwargs):
        """
        Load the page for a named URL and check it was successful.
        """
        page = page or self.page
        response = page.goto(self.url(name, **kwargs))
        self.assertIsNotNone(response)
        self.assertLess(response.status, 400, f"{name} returned HTTP {response.status}")
        return response

    def login(self, user):
        """
        Log the browser in as this user without going through the login form.
        """
        self.client.force_login(user)
        session_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME]
        self.context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": session_cookie.value,
                    "url": self.live_server_url,
                }
            ]
        )

    @staticmethod
    def create_survey(**kwargs) -> tuple[Survey, User]:
        """
        Create an active, fully configured survey and return it with its organisation admin.
        """
        survey = SORT.test.model_factory.SurveyFactory(**kwargs)
        user = survey.project.organisation.members.first()
        survey_service.initialise_survey(user, survey.project, survey)
        # Create the evidence gathering and improvement plan sections, as saving the configuration does
        survey_service.update_consent_demography_config(
            user,
            survey,
            consent_config=survey.consent_config,
            demography_config=survey.demography_config,
            survey_body_path=survey.survey_body_path,
        )
        return survey, user
