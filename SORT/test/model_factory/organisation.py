import factory

from home.models import Organisation


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation
        django_get_or_create = ("name", "description")

    name = factory.Sequence(lambda n: f"Organisation {n}")
    description = factory.Sequence(lambda n: f"Organisation description {n}")
