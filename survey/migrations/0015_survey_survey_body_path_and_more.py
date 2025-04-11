# Generated by Django 5.1.4 on 2025-04-11 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("survey", "0014_merge_20250406_1540"),
    ]

    operations = [
        migrations.AddField(
            model_name="survey",
            name="survey_body_path",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="surveyevidencesection",
            name="section_id",
            field=models.IntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name="surveyevidencesection",
            index=models.Index(
                fields=["section_id"], name="survey_surv_section_4a096b_idx"
            ),
        ),
    ]
