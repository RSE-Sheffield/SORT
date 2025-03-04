# Generated by Django 5.1.2 on 2025-01-16 12:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_alter_organisationmembership_role_guestprojectaccess'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisationmembership',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Admin'), ('PROJECT_MANAGER', 'Project Manager')], default='PROJECT_MANAGER', max_length=20),
        ),
        migrations.CreateModel(
            name='ProjectManagerPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.CharField(choices=[('VIEW', 'View Only'), ('EDIT', 'View and Edit')], default='VIEW', max_length=10)),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('granted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_permissions', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Project manager permissions',
                'unique_together': {('user', 'project')},
            },
        ),
        migrations.DeleteModel(
            name='GuestProjectAccess',
        ),
    ]
