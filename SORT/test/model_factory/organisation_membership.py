import factory.django

from home.models import OrganisationMembership
from .user import UserFactory


class OrganisationMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationMembership

    user = factory.SubFactory(UserFactory, first_name="Admin User")
