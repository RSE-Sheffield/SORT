import factory.django

from home.models import Project

from .organisation import OrganisationFactory


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Sequence(lambda n: f"Project description {n}")
    organisation = factory.SubFactory(OrganisationFactory)
