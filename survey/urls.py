from django.urls import path
from . import views

urlpatterns = [
    path('questionnaire/<int:pk>/', views.QuestionnaireView.as_view(), name='questionnaire'),
    path('completion/', views.CompletionView.as_view(), name='completion_page')
]