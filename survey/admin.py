from django.contrib import admin

from .models import Answer, Question, Questionnaire

admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(Answer)
