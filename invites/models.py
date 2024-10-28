import secrets
from django.db import models
from django.utils import timezone
from survey.models import Questionnaire

class Invitation(models.Model):

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation for {self.questionnaire.title}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(days=7)
