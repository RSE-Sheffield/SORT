from django.contrib import admin

from .models import Invitation, Survey, SurveyResponse


class InvitationAdmin(admin.ModelAdmin):
    list_display = ("survey", "token", "created_at", "used")
    search_fields = ("token",)
    ordering = ("created_at",)


admin.site.register(Survey)
admin.site.register(SurveyResponse)
admin.site.register(Invitation, InvitationAdmin)
