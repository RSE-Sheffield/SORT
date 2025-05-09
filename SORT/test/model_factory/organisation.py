import factory.django

from home.constants import ROLE_ADMIN
from home.models import Organisation

from .organisation_membership import OrganisationMembershipFactory


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Organisation {n}")
    description = factory.Sequence(lambda n: f"Organisation description {n}")
    # Create an administrator user
    # https://factoryboy.readthedocs.io/en/stable/recipes.html#reverse-dependencies-reverse-foreignkey
    members = factory.RelatedFactory(
        OrganisationMembershipFactory,
        factory_related_name="organisation",
        role=ROLE_ADMIN,
    )
