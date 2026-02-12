from django.contrib import admin

from .models import AdminAuditLog, Organisation, OrganisationMembership, Project, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "is_superuser",
                    "organisation_count", "project_count", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    def organisation_count(self, obj):
        """Number of organisations user belongs to"""
        return obj.organisation_set.count()
    organisation_count.short_description = "Orgs"

    def project_count(self, obj):
        """Number of projects user has access to"""
        return sum(1 for _ in obj.projects_iter())
    project_count.short_description = "Projects"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing user
            return self.readonly_fields + ("email",)
        return self.readonly_fields


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "member_count", "project_count", "survey_count", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "Members"

    def project_count(self, obj):
        return obj.projects.count()
    project_count.short_description = "Projects"

    def survey_count(self, obj):
        from survey.models import Survey
        return Survey.objects.filter(project__organisation=obj).count()
    survey_count.short_description = "Surveys"


@admin.register(OrganisationMembership)
class OrganisationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("user__email", "organisation__name")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "created_by", "created_at", "organisation")
    search_fields = ("name", "description",)
    list_filter = ("organisation",)


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "performed_by", "action_type", "target_model", "target_representation")
    list_filter = ("action_type", "target_model", "timestamp")
    search_fields = ("target_representation", "reason", "performed_by__email")
    readonly_fields = ("performed_by", "action_type", "timestamp", "target_model",
                       "target_id", "target_representation", "reason", "metadata")
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False  # Logs created programmatically only

    def has_delete_permission(self, request, obj=None):
        return False  # Immutable

    def has_change_permission(self, request, obj=None):
        return False  # View only
