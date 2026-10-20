import factory.django

from home.models import OrganisationJoinRequest

from .organisation import OrganisationFactory
from .user import UserFactory


class OrganisationJoinRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganisationJoinRequest

    user = factory.SubFactory(UserFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    status = OrganisationJoinRequest.Status.PENDING
    message = factory.Sequence(lambda n: f"Please add me to your organisation {n}")
