from django.contrib import admin

from .models import Organisation, OrganisationMembership, Project, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("-date_joined",)


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "created_at")
    search_fields = (
        "name",
        "description",
    )
    ordering = ("name",)


@admin.register(OrganisationMembership)
class OrganisationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("user__email", "organisation__name")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "created_by", "created_at", "organisation")
    search_fields = (
        "name",
        "description",
    )
    list_filter = ("organisation",)
