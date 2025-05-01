import factory.django

from .organisation import OrganisationFactory
from home.models import Project


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Sequence(lambda n: f"Project description {n}")
    organisation = factory.SubFactory(OrganisationFactory)
