# Import test data

Run:

```bash
python manage.py loaddata ./data/001_users.json ./data/002_organisations.json ./data/003_memberships.json ./data/004_projects.json ./data/005_project_organisations.json ./data/006_project_managers.json ./data/007_surveys.json ./data/008_survey_responses.json
```

The password for users is their respective role name in lowercases.
