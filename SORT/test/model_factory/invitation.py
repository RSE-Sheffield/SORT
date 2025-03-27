import factory.django

from survey.models import Invitation


class InvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invitation

