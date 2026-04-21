[![Run Django checks](https://github.com/RSE-Sheffield/SORT/actions/workflows/django-check.yaml/badge.svg)](https://github.com/RSE-Sheffield/SORT/actions/workflows/django-check.yaml)

# SORT
### Self-Assessment of Organisational Readiness Tool

The SORT provides a comprehensive self-assessment framework, enabling organisations to evaluate and strengthen their research capabilities within nursing and 
broader health and care practices. By guiding you through forty-four targeted statements, SORT helps assess your current level of research maturity 
and the support available for nurses involved in research. Upon completion, your organisation will be equipped to create a tailored improvement plan to better 
integrate research into nursing practice, ultimately contributing to improved patient care.


## Running Locally

Follow these steps to set up and run the app locally:

Prerequisites, ensure the following are already installed on your system:

- Python (the version is defined [.python-version](./.python-version))
- pip
- Nodejs (20.x)
---

1. Clone the project repository to your local machine
```bash
git clone <repository-url>
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/Scripts/activate
```

3. Install dependencies
```bash
# Install python requirements
pip install -r requirements.txt
# Install nodejs requirements
npm install
```

4. Configure the database

```bash
python manage.py migrate
```

5. Create a superuser
```bash
python manage.py createsuperuser
```

6. Create a `.env` file in the project root directory and add the following environment variables (which should be used in development only)

```bash
cp .env.example .env
```

7. Finally, start the development server

```bash
python manage.py runserver
```

8. Start the vite javascript server (in a different terminal)
```bash
npm run dev
```

The app will be available at http://127.0.0.1:8000.

9. Import test data by following the instructions as [`data/README.md`](./data/README.md).

# Deployment

Please read [`docs/deployment.md`](docs/deployment.md).


# Vite integration
The SORT app uses some JavaScript components such as the survey configurator and the survey response form. This is
implemented using the svelte framework and vite is used as the bundler. [Vite](https://vite.dev/) also provides a live server for development which includes HMR (hot module reloading).

In order to integrate this into the HTML template, a [custom template tag](https://docs.djangoproject.com/en/5.1/howto/custom-template-tags/) library is created at `/home/templatetags/vite_integration.py`.
- The `vite_client` template tag is used to include Vite's HMR JavaScript code. 
- The `vite_asset` tag is used to include asset files (e.g. TypeScript files) in the template.
  - In debug mode, this creates a link directly to the Vite dev server normally located at `http://localhost:5173`
  - In production mode, the link changes to the location of the file in the `/static/` folder

For more information, please [read the README](ui-components/README.md).

## Installation

Install the JavaScript package using [`npm install`](https://docs.npmjs.com/cli/v8/commands/npm-install/)

```bash
npm install
```

## Usage

The development mode will run the test page at http://localhost:5173

```bash
npm run dev
```

## Before deployment

The script files within `./ui_components/` must be built into the static folder before deployment. This
can be done by running:

```bash
npm run build
```

This will transpile the typescript files and write them into `/static/ui-components/` folder.

Then run django's `collectstatic` to gather all files into the static folder.

```bash
python manage.py collectstatic
```
