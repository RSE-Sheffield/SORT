import secrets
from django.db import models
from django.urls import reverse
from django.utils import timezone
from home.models import Project

class Survey(models.Model):
    """
    Represents a survey that will be sent out to a participant
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    survey_config = models.JSONField(null=True)
    consent_config = models.JSONField(null=True)
    demography_config = models.JSONField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("survey", kwargs={"pk": self.pk})


class SurveyResponse(models.Model):
    """
    Represents a single response to the survey from a participant
    """

    survey = models.ForeignKey(Survey, related_name='survey_response', on_delete=models.CASCADE)  # Many questions belong to one survey
    answers = models.JSONField()

    def get_absolute_url(self, token):
        return reverse('survey', kwargs={'pk': self.pk, 'token': token})



class Invitation(models.Model):

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation for {self.survey.name}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(days=7)
