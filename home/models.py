from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from survey.models import Questionnaire

class UserManager(BaseUserManager):
    def create_user(self, firstname, lastname, email, organisation, password=None):

        if not email:

            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(email=email, firstname=firstname, lastname=lastname, organisation=organisation)

        user.set_password(password) # this hashes the password

        user.save(using=self.db)

        return user

    def create_superuser(self, email, firstname, lastname, organisation, password=None):
        user = self.create_user(email=email, firstname=firstname,
            lastname=lastname, organisation=organisation, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class Organisation(models.Model):

    name = models.CharField(max_length=200)

    # one organisation can have many users
    users = models.ManyToManyField('User', blank=True)

    projects = models.ForeignKey('Project', on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.name

class Project(models.Model):

    name = models.CharField(max_length=100)

    #one to many relationship with organisation
    organisations = models.ForeignKey('Organisation', on_delete=models.CASCADE, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)

    surveys = models.ManyToManyField(Questionnaire, blank=True)

    def __str__(self):
        return self.name

class User(AbstractBaseUser):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    organisations = models.ForeignKey('Organisation', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="user")

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstname','lastname', 'organisation']

    objects = UserManager()

    def __str__(self):
        return f'{self.firstname} {self.lastname}'
