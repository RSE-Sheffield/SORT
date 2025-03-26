from django.contrib import admin

from .models import Invitation, Survey, SurveyResponse, SurveyEvidenceSection, SurveyFile, SurveyEvidenceFile


class InvitationAdmin(admin.ModelAdmin):
    list_display = ("survey", "token", "created_at", "used")
    search_fields = ("token",)
    ordering = ("created_at",)


admin.site.register(Survey)
admin.site.register(SurveyResponse)
admin.site.register(SurveyEvidenceSection)
admin.site.register(SurveyFile)
admin.site.register(SurveyEvidenceFile)
admin.site.register(Invitation, InvitationAdmin)
