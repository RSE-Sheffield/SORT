# SORT testing

There are three kinds of tests: frontend unit tests (JavaScript and Node.js), backend tests (Python Django), and end-to-end browser tests that exercise the whole app.

There is a testing script for Windows at [scripts/test.bat](../scripts/test.bat).

# Frontend testing

## Usage

To run the test suite, use the `test` command via the Node package manager (NPM):

```bash
npm test
```

This will execute Vitest. There are also other testing modes. To run the tests whenever the code changes using a file watcher, run:

```bash
npm run test:watch
```

And to get a coverage report:

```bash
npm run test:coverage
```

## Writing tests

The frontend tests are contained in the `ui_components/tests` directory and are organised to match the source code structure. Each test should test an isolated unit of code. Please read the [introduction to writing tests for Svelte](https://svelte.dev/docs/svelte/testing) and the [Svelte testing library](https://testing-library.com/docs/svelte-testing-library/intro).

# Backend testing

The test suite uses the Django testing tools. For more information, please read [Testing in Django](https://docs.djangoproject.com/en/5.1/topics/testing/) and
the further [Django testing examples](https://django-testing-docs.readthedocs.io/en/latest/index.html).

## Installation

To install the necessary packages in your local development environment, use the `requirements-dev.txt` file.

```bash
pip install --upgrade --requirement requirements-dev.txt
```

## Usage

### Running the test suite

Pleaser read the [running tests](https://docs.djangoproject.com/en/5.1/topics/testing/overview/#running-tests) section of the Django documentation.

```bash
python manage.py test home/tests --parallel=auto --failfast
python manage.py test survey/tests --parallel=auto --failfast
```

### Coverage reports

At the end of the GitHub Actions testing workflow, a coverage report will be generated using the [Coverage.py](https://coverage.readthedocs.io/) tool.

## Writing tests

Please read the Django [writing tests section](https://docs.djangoproject.com/en/5.1/topics/testing/overview/#writing-tests) of the Django documentation. There are unit tests in the `./tests` directory of each Django application.

### Tests

The tests are defined in each application in the `tests` directory, where each file is a Python script that contains tests for a different aspect of the app. The filenames must start with `test_`.

### Test cases

There are test case classes defined in the [`SORT.test.test_case`](SORT/test/test_case) module that contain useful methods for testing Django views and the application service layer in the SORT code.

### Object factories

There are factory utilities that are used to create mock objects of our Django models for testing in the [`SORT.test.model_factory`](SORT/test/model_factory) module. This uses the [Factory Boy](https://factoryboy.readthedocs.io/en/stable/index.html) library, which [supports the Django ORM](https://factoryboy.readthedocs.io/en/stable/orms.html#module-factory.django).

# End-to-end testing

The end-to-end tests in the [`e2e`](../e2e) directory run the real Django app, with the built Svelte front end, in a headless Chromium browser using [Playwright for Python](https://playwright.dev/python/). They focus on the key user journeys, especially survey capture, rather than aiming for full coverage:

- `test_smoke.py` loads each key page, checks it renders, and that the Svelte components mount
- `test_survey_response.py` generates an invitation link and completes a survey as a respondent, including validation and page navigation
- `test_survey_configure.py` adds a demographic question and checks respondents see it
- `test_evidence_improvement.py` saves an evidence statement, uploads evidence and saves an improvement plan
- `test_auth.py` covers the login form

Every test automatically fails if the browser reports an uncaught JavaScript exception or a console error, or if the server returns an HTTP 5xx response.

## Installation

Install the development packages (see above), then download the browser and build the front-end assets:

```bash
playwright install chromium
npm run build
```

Rebuild the front end (`npm run build`) whenever the Svelte code changes, because the tests use the built assets rather than the Vite development server.

## Usage

```bash
make e2e
# or
python manage.py test e2e
```

The tests are tagged `e2e` and are excluded from `make test`. They are skipped if Playwright isn't installed or the front end hasn't been built.

To watch the browser while the tests run, set `E2E_HEADED=1`. When a test fails, screenshots of the open pages are saved to the `test-results/` directory (these are also uploaded as an artifact by the GitHub Actions workflow).

## Writing tests

Extend `e2e.base.PlaywrightTestCase`, which provides:

- `self.page`: a Playwright page, and `self.new_anonymous_page()` for a separate, logged-out browser session
- `self.login(user)`: log in without using the login form
- `self.visit(url_name, **kwargs)`: open a page by its URL name and check the response is successful
- `self.create_survey()`: create a fully configured survey and return it with its organisation administrator

The helpers in `e2e/survey.py` fill in the survey response form based on the survey configuration. Prefer user-facing locators such as `get_by_role` and `get_by_label` (see [Playwright locators](https://playwright.dev/python/docs/locators)).
