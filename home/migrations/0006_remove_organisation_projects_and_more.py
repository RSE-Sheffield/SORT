# Generated by Django 5.1.2 on 2025-01-10 13:12

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('home', '0005_rename_firstname_user_first_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisation',
            name='projects',
        ),
        migrations.RemoveField(
            model_name='organisation',
            name='users',
        ),
        migrations.RemoveField(
            model_name='user',
            name='organisations',
        ),
        migrations.AddField(
            model_name='organisation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='date_joined',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.RemoveField(
            model_name='project',
            name='organisations',
        ),
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
        migrations.CreateModel(
            name='OrganisationMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Administrator'), ('MEMBER', 'Member'), ('GUEST', 'Guest')], default='GUEST', max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.organisation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'organisation')},
            },
        ),
        migrations.AddField(
            model_name='organisation',
            name='members',
            field=models.ManyToManyField(through='home.OrganisationMembership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ProjectOrganisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.organisation')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.project')),
            ],
            options={
                'unique_together': {('project', 'organisation')},
            },
        ),
        migrations.AddField(
            model_name='project',
            name='organisations',
            field=models.ManyToManyField(through='home.ProjectOrganisation', to='home.organisation'),
        ),
    ]
