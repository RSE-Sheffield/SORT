import factory.django

from survey.models import Invitation

from .survey import SurveyFactory


class InvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invitation

    survey = factory.SubFactory(SurveyFactory)
