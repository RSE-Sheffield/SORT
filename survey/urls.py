from django.urls import path

from . import views

urlpatterns = [
    path("survey/<int:pk>", views.SurveyView.as_view(), name="survey"),
    path(
        "survey/<int:pk>/configure",
        views.SurveyConfigureView.as_view(),
        name="survey_configure",
    ),
    path(
        "survey/<int:pk>/delete/",
        views.SurveyDeleteView.as_view(),
        name="survey_delete",
    ),
    path(
        "survey/<int:pk>/create_invite",
        views.SurveyCreateInviteView.as_view(),
        name="suvey_create_invite",
    ),
    path(
        "survey/<int:pk>/mock_responses",
        views.SurveyGenerateMockResponsesView.as_view(),
        name="survey_mock_responses",
    ),
    path(
        "survey/<int:pk>/export", views.SurveyExportView.as_view(), name="survey_export"
    ),
    path(
        "survey/<int:pk>/evidence_gathering",
        views.SurveyEvidenceGatheringView.as_view(),
        name="survey_evidence_gathering",
    ),
    path(
        "survey/<int:pk>/improvement_plan",
        views.SurveyImprovementPlanView.as_view(),
        name="survey_improvement_plan",
    ),
    path(
        "survey/create/<int:project_id>",
        views.SurveyCreateView.as_view(),
        name="survey_create",
    ),
    path("completion/", views.CompletionView.as_view(), name="completion_page"),
    path(
        "survey_response/<str:token>",
        views.SurveyResponseView.as_view(),
        name="survey_response",
    ),
    path(
        "survey_link_invalid/",
        views.SurveyLinkInvalidView.as_view(),
        name="survey_link_invalid",
    ),
    path("invite/<int:pk>", views.InvitationView.as_view(), name="invite"),
    path(
        "invite/success/",
        views.SuccessInvitationView.as_view(),
        name="success_invitation",
    ),
]
