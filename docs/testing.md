# SORT testing

See: [Testing in Django](https://docs.djangoproject.com/en/5.1/topics/testing/) and
further [Django testing examples](https://django-testing-docs.readthedocs.io/en/latest/index.html).

There are unit tests in the `./tests` directory of each Django app. See [writing tests](https://docs.djangoproject.com/en/5.1/topics/testing/overview/#writing-tests).

# Installation

To install the necessary packages in your local development environment, use the `requirements-dev.txt` file.

```bash
pip install --upgrade --requirement requirements-dev.txt
```

# Usage

## Running the test suite

[Running Django tests](https://docs.djangoproject.com/en/5.1/topics/testing/overview/#running-tests)

```bash
python manage.py test home/tests --parallel=auto
python manage.py test survey/tests --parallel=auto
```

# Writing tests

## Tests

The tests are defined in each application in the `tests` directory, where each file is a Python script that contains tests for a different aspect of the app. The filenames must start with `test_`.

## Test cases

There are test case classes defined in the [`SORT.test.test_case`](SORT/test/test_case) module that contain useful methods for testing Django views and the application service layer in the SORT code.

## Object factories

There are factory utilitise that are used to create mock objects of our Django models for testing in the [`SORT.test.model_factory`](SORT/test/model_factory) module.