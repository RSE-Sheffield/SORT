import django.contrib.auth
import factory

from .constants import PASSWORD


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django.contrib.auth.get_user_model()
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@sort.com")
    first_name = factory.Sequence(lambda n: f"User{n}")
    last_name = factory.Sequence(lambda n: f"Lastname{n}")
    password = factory.PostGenerationMethodCall("set_password", PASSWORD)
