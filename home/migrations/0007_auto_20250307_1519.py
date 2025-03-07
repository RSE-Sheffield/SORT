# Generated by Django 5.1.4 on 2025-03-07 15:19

from django.db import migrations, models
import django.db.models.deletion


def migrate_project_organisations(apps, schema_editor):
    """
    For each project, keep only the first organization relationship and set it as the direct FK
    """
    Project = apps.get_model("yourappname", "Project")
    ProjectOrganisation = apps.get_model("yourappname", "ProjectOrganisation")

    # For each project
    for project in Project.objects.all():
        # Get the first project-org relationship
        first_org_relation = (
            ProjectOrganisation.objects.filter(project=project)
            .select_related("organisation")
            .first()
        )

        if first_org_relation:
            # Set the organisation field directly on the project
            project.organisation = first_org_relation.organisation
            project.save()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_project_description"),
    ]


operations = [
    # 1. Add the new organisation ForeignKey to Project model
    migrations.AddField(
        model_name="project",
        name="organisation",
        field=models.ForeignKey(
            null=True,  # Allow null temporarily during migration
            on_delete=django.db.models.deletion.CASCADE,
            related_name="projects",
            to="yourappname.organisation",
        ),
    ),
    # 2. Run data migration to populate the new field
    migrations.RunPython(migrate_project_organisations),
    # 3. Make the organisation field required
    migrations.AlterField(
        model_name="project",
        name="organisation",
        field=models.ForeignKey(
            null=False,
            on_delete=django.db.models.deletion.CASCADE,
            related_name="projects",
            to="yourappname.organisation",
        ),
    ),
    # 4. Remove the ProjectOrganisation model and relationships
    migrations.RemoveField(
        model_name="projectorganisation",
        name="added_by",
    ),
    migrations.RemoveField(
        model_name="projectorganisation",
        name="organisation",
    ),
    migrations.RemoveField(
        model_name="projectorganisation",
        name="project",
    ),
    migrations.DeleteModel(
        name="ProjectOrganisation",
    ),
    # 5. Remove the redundant ProjectManagerPermission model as all project managers can see all projects
    migrations.RemoveField(
        model_name="projectmanagerpermission",
        name="granted_by",
    ),
    migrations.RemoveField(
        model_name="projectmanagerpermission",
        name="project",
    ),
    migrations.RemoveField(
        model_name="projectmanagerpermission",
        name="user",
    ),
    migrations.DeleteModel(
        name="ProjectManagerPermission",
    ),
]
