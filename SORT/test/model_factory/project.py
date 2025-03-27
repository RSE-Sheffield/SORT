import factory.django

from home.models import Project


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        django_get_or_create = ("name", "description", "organisation")

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Sequence(lambda n: f"Project description {n}")
