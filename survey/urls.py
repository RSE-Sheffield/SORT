from django.urls import path

from . import views

urlpatterns = [
    path('survey/<int:pk>', views.SurveyView.as_view(), name='survey'),
    path('completion/', views.CompletionView.as_view(), name='completion_page'),
    path('survey_response/<int:pk>/<str:token>', views.SurveyResponseView.as_view(), name='survey_response'),
    path('survey_link_invalid/', views.SurveyLinkInvalidView.as_view(), name='survey_link_invalid'),
    path('invite/', views.InvitationView.as_view(), name='invite'),
    path('invite/success/', views.SuccessInvitationView.as_view(), name='success_invitation'),

]
