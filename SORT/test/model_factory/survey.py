import factory

from survey.models import Survey


class SurveyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Survey
        django_get_or_create = ("name", "description")

    name = factory.Sequence(lambda n: f"Survey {n}")
    description = factory.Sequence(lambda n: f"Survey description {n}")
