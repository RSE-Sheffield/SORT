# Import test data

Run the [`loaddata` command](https://docs.djangoproject.com/en/5.1/ref/django-admin/#loaddata) to load in all
of the mocked test data:
.

```bash
python manage.py loaddata ./data/*.json
```

or the following if you're using Powershell:

```powershell
$files = Get-ChildItem -Path "data" -Filter "*.json"

foreach ($file in $files) {
  python manage.py loaddata $file.FullName
}

The password for users is their respective role name in lowercases.

