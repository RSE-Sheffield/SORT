# Generated by Django 5.1.2 on 2025-01-14 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
