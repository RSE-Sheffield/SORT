import factory

from .user import UserFactory


class SuperUserFactory(UserFactory):
    is_superuser = True
    is_staff = True
    first_name = factory.Sequence(lambda n: f"Superuser{n}")
    email = factory.Sequence(lambda n: f"superuser{n}@sort.com")
