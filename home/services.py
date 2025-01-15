from .models import GuestProjectAccess, Project, User


class ProjectAccessService:
    """
    Service class for managing project access
    """
    
    @staticmethod
    def grant_guest_access(project: Project, guest_user: User, granted_by: User, permission ="VIEW"):
        if permission not in ["VIEW", "EDIT"]:
            raise ValueError("Permission must be either VIEW or EDIT")

        if not guest_user.organisationmembership_set.filter(
            organisation__projectorganisation__project=project,
            role="GUEST"
        ).exists():
            raise ValueError("User must be a guest in one of the project's organisations")
            
        return GuestProjectAccess.objects.update_or_create(
            user=guest_user,
            project=project,
            defaults={
                'granted_by': granted_by,
                'permission': permission
            }
        )

    @staticmethod
    def revoke_guest_access(project, guest_user):
        return GuestProjectAccess.objects.filter(
            user=guest_user,
            project=project
        ).delete()