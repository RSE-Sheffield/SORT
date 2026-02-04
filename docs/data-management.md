# Data management

# Data export

Data can be exported using the [dumpdata](https://docs.djangoproject.com/en/5.2/ref/django-admin/#dumpdata) management command.

First, set up the shell

```bash
sort_dir="/opt/sort"
python="$sort_dir/venv/bin/python"

cd "$sort_dir"
```

Run the command and pipe the entire database contents in JSON format to a file.

```bash
sudo $python -Xutf8 $sort_dir/manage.py dumpdata --all --format json --output="/tmp/sort-dumpdata.json"
```

We need to use the `-Xutf8` command-line option for Python to force the use of  UTF-8 encoding so that special characters are handled properly when writing to a file. For some reason the system is using `latin-1` encoding.
