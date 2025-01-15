[![Run Django checks](https://github.com/RSE-Sheffield/SORT/actions/workflows/django-check.yaml/badge.svg)](https://github.com/RSE-Sheffield/SORT/actions/workflows/django-check.yaml)
# SORT
### Self-Assessment of Organisational Readiness Tool


The SORT provides a comprehensive self-assessment framework, enabling organisations to evaluate and strengthen their research capabilities within nursing and 
broader health and care practices. By guiding you through forty-four targeted statements, SORT helps assess your current level of research maturity 
and the support available for nurses involved in research. Upon completion, your organisation will be equipped to create a tailored improvement plan to better 
integrate research into nursing practice, ultimately contributing to improved patient care.


## Running Locally

Follow these steps to set up and run the app locally:

---

Prerequisites

- Python 3.10
- pip
---

1. Clone the project repository to your local machine
```bash
git clone <repository-url>
```

---

2. Create and activate a virtual environment
```bash
python -m venv .venv

source .venv/Scripts/activate

```

---

3. Install dependencies
```bash
pip install -r requirements.txt
```

---

4. Configure the database

```bash
python manage.py migrate
```

---

5. Create a superuser
```bash
python manage.py createsuperuser
```

---

6. Create a `.env` file in the project root directory and add the following environment variables:

```
DJANGO_SECRET_KEY=your_secret_key
```

---

7. Finally, run start the development server
```bash
python manage.py runserver
```

The app will be available at http://127.0.0.1:8000.

---

8. Import data using the [`loaddata`](https://docs.djangoproject.com/en/5.1/ref/django-admin/#django-admin-loaddata) command

```bash
python manage.py loaddata data\questionnaires.json data\questionnaires.json
```
