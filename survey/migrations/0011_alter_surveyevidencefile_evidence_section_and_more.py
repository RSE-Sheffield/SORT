# Generated by Django 5.1.4 on 2025-03-29 14:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("survey", "0010_rename_surveyevidencesectionfile_surveyevidencefile_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="surveyevidencefile",
            name="evidence_section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="evidence_files",
                to="survey.surveyevidencesection",
            ),
        ),
        migrations.AlterField(
            model_name="surveyfile",
            name="survey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="survey.survey",
            ),
        ),
    ]
