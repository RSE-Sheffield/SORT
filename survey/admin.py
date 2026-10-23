from django.contrib import admin

from .models import (
    Invitation,
    Survey,
    SurveyEvidenceFile,
    SurveyEvidenceSection,
    SurveyFile,
    SurveyResponse,
)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("survey", "token", "created_at", "used")
    search_fields = ("token",)
    ordering = ("created_at",)


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "created_at",
        "project",
        "project__organisation",
        "responses_count",
    )
    search_fields = (
        "name",
        "description",
    )
    ordering = ("created_at",)
    list_filter = (
        "project",
        "project__organisation",
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Answers are stored by position, so the questions can't change once responses exist.
        """
        readonly = super().get_readonly_fields(request, obj)
        if obj is not None and obj.has_responses:
            return (*readonly, "survey_config")
        return readonly


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "survey",
        "created_at",
        "survey__project",
        "survey__project__organisation",
    )
    ordering = ("created_at",)
    date_hierarchy = "created_at"
    list_filter = ("survey__project", "survey__project__organisation", "created_at")


admin.site.register(SurveyEvidenceSection)
admin.site.register(SurveyFile)
admin.site.register(SurveyEvidenceFile)
