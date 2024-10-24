from django.urls import path
from . import views

urlpatterns = [
    path('survey/<int:pk>/<str:token>/', views.QuestionnaireView.as_view(), name='questionnaire'),
    path('completion/', views.CompletionView.as_view(), name='completion_page')
]