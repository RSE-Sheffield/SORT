from django.contrib import admin

from .models import (
    Organisation,
    OrganisationMembership,
    Project,
    ProjectOrganisation,
    User,
)


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("-date_joined",)


class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


class OrganisationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("user__email", "organisation__name")


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_on")
    search_fields = ("name",)
    list_filter = ("created_on",)


class ProjectOrganisationAdmin(admin.ModelAdmin):
    list_display = ("project", "organisation", "added_by", "added_at")
    search_fields = ("project__name", "organisation__name")


admin.site.register(User, UserAdmin)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(OrganisationMembership, OrganisationMembershipAdmin)
admin.site.register(ProjectOrganisation, ProjectOrganisationAdmin)
