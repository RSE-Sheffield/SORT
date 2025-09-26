from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.urls import reverse

from .constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER, ROLES


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, password=None):
        if not email:
            raise ValueError("Email is required")
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None):
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        # If they didn't enter their name, default to email address
        if not self.first_name and not self.last_name:
            return self.email
        return f"{self.first_name} {self.last_name}"

    @property
    def active_projects(self) -> int:
        """
        Count the number of active surveys associated with this user.
        """
        active_surveys = 0
        for project in self.projects_iter():
            if project.is_active:
                active_surveys += 1

        return active_surveys

    def projects_iter(self):
        """
        Iterate over all this user's projects.
        """
        for organisation in self.organisation_set.all():
            yield from organisation.projects.all()


class Organisation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(
        User, through="OrganisationMembership", through_fields=("organisation", "user")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_user_role(self, user: User):
        if user.is_superuser or user.is_staff:
            return ROLE_ADMIN

        membership = self.organisationmembership_set.filter(user=user).first()

        return membership.role if membership else None


class OrganisationMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default=ROLE_PROJECT_MANAGER)
    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="members_added", null=True
    )

    class Meta:
        unique_together = ["user", "organisation"]


class Project(models.Model):
    """
    A project is an organisation unit for surveys within an organisation.
    """
    name = models.CharField(max_length=100, help_text="Project title")
    description = models.TextField(blank=True, null=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="projects"
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project", kwargs={"project_id": self.pk})

    @property
    def is_active(self) -> bool:
        """
        Does this project contain any active surveys?
        """
        return any(self.survey.values_list("is_active", flat=True))
