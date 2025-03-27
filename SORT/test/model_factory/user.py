import django.contrib
import factory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django.contrib.auth.get_user_model()
        django_get_or_create = ("email", "first_name", "last_name")

    email = factory.Sequence(lambda n: f"user{n}@sort.com")
    first_name = factory.Sequence(lambda n: f"User{n}")
    last_name = factory.Sequence(lambda n: f"Lastname{n}")
