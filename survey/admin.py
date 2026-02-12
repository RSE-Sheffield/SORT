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
    list_display = ("pk", "name", "is_shared", "is_active", "responses_count",
                    "created_at", "project", "project__organisation")
    search_fields = ("name", "description", "project__name", "project__organisation__name")
    ordering = ("-created_at",)
    list_filter = ("is_shared", "is_active", "survey_body_path", "project__organisation", "created_at")
    readonly_fields = ("created_at", "survey_config")


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("pk", "survey", "created_at", "survey__project", "survey__project__organisation",)
    ordering = ("created_at",)
    date_hierarchy = "created_at"
    list_filter = ("survey__project", "survey__project__organisation", "created_at")


admin.site.register(SurveyEvidenceSection)
admin.site.register(SurveyFile)
admin.site.register(SurveyEvidenceFile)
