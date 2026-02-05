# SORT testing

There are two testing frameworks in place: one for the frontend (JavaScript and Node.js) and another for the backend (Python Django).

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