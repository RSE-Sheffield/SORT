# Generated by Django 5.1.1 on 2024-10-01 16:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("survey", "0003_alter_question_question_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="questionnaire",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="survey.questionnaire",
            ),
        ),
    ]
