from django.db import models
from django.urls import reverse


class Questionnaire(models.Model):
    # Questionnaire data model
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

    def get_absolute_url(self, token):
        return reverse("survey", kwargs={"pk": self.pk, "token": token})


class Question(models.Model):
    # Question data model
    QUESTION_TYPE_CHOICES = [
        ("text", "Text"),
        ("multiple_choice", "Multiple Choice"),
        ("rating", "Rating"),
        ("boolean", "Agree/Disagree"),
    ]

    questionnaire = models.ForeignKey(
        Questionnaire, related_name="questions", on_delete=models.CASCADE
    )  # Many questions belong to one questionnaire
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(
        max_length=50, choices=QUESTION_TYPE_CHOICES, default="multiple_choice"
    )

    def __str__(self):
        return self.question_text


class Answer(models.Model):
    # User answer data model
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    token = models.CharField(max_length=64, blank=True, editable=False)
    submitted_at = models.DateTimeField(null=True)  #

    def __str__(self):
        return f"Answer for {self.question.question_text}"


class Comment(models.Model):
    # Comments data model
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, blank=True, editable=False)
    text = models.TextField()
    submitted_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"Comment on {self.questionnaire.title}"
