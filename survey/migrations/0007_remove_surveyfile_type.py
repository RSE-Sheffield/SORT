# Generated by Django 5.1.4 on 2025-03-24 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("survey", "0006_surveyfile"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="surveyfile",
            name="type",
        ),
    ]
