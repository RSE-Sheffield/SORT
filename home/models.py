from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.urls import reverse
from .constants import ROLES, ROLE_ADMIN, ROLE_MEMBER, ROLE_GUEST, RoleType


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
        return f"{self.first_name} {self.last_name}"


class Organisation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(User, through="OrganisationMembership")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_user_role(self, user):
        membership = self.organisationmembership_set.filter(user=user).first()
        return membership.role if membership else None


class OrganisationMembership(models.Model):
    ROLE_CHOICES = ROLES

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default=ROLE_GUEST)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "organisation"]
        """ A user can only be a member of an organisation once """


class Project(models.Model):
    name = models.CharField(max_length=100)
    organisations = models.ManyToManyField(Organisation, through="ProjectOrganisation")
    """ A project can be associated with multiple organisations/teams """
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_guest_users(self):
        return GuestProjectAccess.objects.filter(project=self).select_related("user")

    def get_absolute_url(self):
        return reverse("project", kwargs={"project_id": self.pk})


class ProjectOrganisation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ["project", "organisation"]


class GuestProjectAccess(models.Model):
    PERMISSION_CHOICES = [
        ("VIEW", "View Only"),
        ("EDIT", "View and Edit"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    permission = models.CharField(
        max_length=10, choices=PERMISSION_CHOICES, default="VIEW"
    )
    granted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="granted_access"
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "project"]
        verbose_name_plural = "Guest project access"
