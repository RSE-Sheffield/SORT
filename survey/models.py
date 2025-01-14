import secrets
from django.db import models
from django.urls import reverse
from django.utils import timezone
from home.models import Project

class Survey(models.Model):
    """
    Represents a survey that will be sent out to a participant
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    survey_config = models.JSONField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self, token):
        return reverse("survey", kwargs={"pk": self.pk, "token": token})


class SurveyResponse(models.Model):
    """
    Represents a single response to the survey from a participant
    """

    survey = models.ForeignKey(Survey, related_name='survey', on_delete=models.CASCADE)  # Many questions belong to one survey
    answers = models.JSONField()

    def get_absolute_url(self, token):
        return reverse('survey', kwargs={'pk': self.pk, 'token': token})



class Invitation(models.Model):

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation for {self.survey.title}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(days=7)
