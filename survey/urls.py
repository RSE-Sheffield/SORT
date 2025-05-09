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
        "survey/<int:pk>/edit",
        views.SurveyEditView.as_view(),
        name="survey_edit",
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
        "survey/<int:pk>/add_file",
        views.SurveyFileUploadView.as_view(),
        name="survey_add_file"
    ),
    path(
        "survey/<int:pk>/export", views.SurveyExportView.as_view(), name="survey_export"
    ),
    path(
        "survey/<int:pk>/response_data",
        views.SurveyResponseDataView.as_view(),
        name="survey_response_data",
    ),
    path(
        "survey/<int:pk>/evidence_gathering/<int:section_id>",
        views.SurveyEvidenceGatheringView.as_view(),
        name="survey_evidence_gathering",
    ),
    path(
        "survey/<int:pk>/evidence_gathering/<int:section_id>/update",
        views.SurveyEvidenceUpdateView.as_view(),
        name="survey_evidence_gathering_update",
    ),
    path(
        "survey/<int:pk>/evidence_gathering/<int:section_id>/add_file",
        views.SurveyEvidenceFileUploadView.as_view(),
        name="survey_evidence_add_file"
    ),
    path(
        "survey_evidence/remove_file/<int:pk>",
        views.SurveyEvidenceFileDeleteView.as_view(),
        name="survey_evidence_remove_file"
    ),
    path(
        "survey_evidence/file/<int:pk>",
        views.SurveyEvidenceFileView.as_view(),
        name="survey_evidence_file"
    ),
    path(
        "survey/<int:pk>/improvement_plan/<int:section_id>",
        views.SurveyImprovementPlanView.as_view(),
        name="survey_improvement_plan",
    ),
    path(
        "survey/<int:pk>/improvement_plan/<int:section_id>/update",
        views.SurveyImprovementPlanUpdateView.as_view(),
        name="survey_improvement_plan_update",
    ),
    path(
        "survey/<int:pk>/report",
        views.SurveyReportView.as_view(),
        name="survey_report",
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
