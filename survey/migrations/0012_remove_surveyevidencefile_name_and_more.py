# Generated by Django 5.1.4 on 2025-03-29 14:36

import django.db.models.deletion
import survey.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("survey", "0011_alter_surveyevidencefile_evidence_section_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="surveyevidencefile",
            name="name",
        ),
        migrations.RemoveField(
            model_name="surveyevidencefile",
            name="path",
        ),
        migrations.RemoveField(
            model_name="surveyfile",
            name="name",
        ),
        migrations.RemoveField(
            model_name="surveyfile",
            name="path",
        ),
        migrations.AddField(
            model_name="surveyevidencefile",
            name="file",
            field=models.FileField(
                blank=True, null=True, upload_to=survey.models.survey_file_upload_path
            ),
        ),
        migrations.AddField(
            model_name="surveyfile",
            name="file",
            field=models.FileField(
                blank=True, null=True, upload_to=survey.models.survey_file_upload_path
            ),
        ),
        migrations.AlterField(
            model_name="surveyevidencefile",
            name="evidence_section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="survey.surveyevidencesection",
            ),
        ),
    ]
