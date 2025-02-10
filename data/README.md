# Import test data

Run the [`loaddata` command](https://docs.djangoproject.com/en/5.1/ref/django-admin/#loaddata).

```bash
python manage.py loaddata ./data/001_users.json ./data/002_organisations.json ./data/003_memberships.json ./data/004_projects.json ./data/005_project_organisations.json ./data/006_project_managers.json ./data/007_surveys.json ./data/008_survey_responses.json
```

The password for users is their respective role name in lowercases.

