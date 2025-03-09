import factory
from django.contrib.auth import get_user_model

from home.models import Organisation, Project
from survey.models import Survey


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('email', 'first_name', 'last_name')


    email = factory.Sequence(lambda n: f'user{n}@sort.com')
    first_name = factory.Sequence(lambda n: f'User{n}')
    last_name = factory.Sequence(lambda n: f'Lastname{n}')

class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation
        django_get_or_create = ('name','description')

    name = factory.Sequence(lambda n: f'Organisation {n}')
    description = factory.Sequence(lambda n: f'Organisation description {n}')


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        django_get_or_create = ('name','description')

    name = factory.Sequence(lambda n: f'Project {n}')
    description = factory.Sequence(lambda n: f'Project description {n}')

class SurveyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Survey
        django_get_or_create = ('name','description')

    name = factory.Sequence(lambda n: f'Survey {n}')
    description = factory.Sequence(lambda n: f'Survey description {n}')
