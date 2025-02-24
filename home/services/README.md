# Permission Management

This folder implements a permission management system that provides role-based access control (RBAC) for organisations and projects. The system implements a flexible permissions model with support for admin and project manager roles, along with granular view/edit permissions at both organisation and project levels.

## Implementation

The current implementation provides:

- Abstract base class `BasePermissionService` with core permission methods
- Permission decorators `requires_permission` for method-level access control for services

Service classes can inherit from `BasePermissionService` to implement custom permission checks. The `requires_permission` decorator can be used to enforce access control at the method level.

Why don't we use Django's built-in permissions system? The Django permissions system is designed for managing access to models and views within a Django application. It is not designed to handle complex permission requirements such as role-based access control (RBAC) across multiple resources. The custom permission management system provides more flexibility and control over access control requirements.

## Permission Model

### Roles

For simplicity, the system supports two roles:

- Admin: Full access to organisation and its projects
- Project Manager: Limited access based on granted permissions. A PM can be granted view and edit permissions for multiple projects within an organisation.

### Permission Levels

View: Read-only access
Edit: Ability to modify resources
Delete: Ability to remove resources
Create: Ability to create new resources


## Usage

```python
@requires_permission("view", obj_param="organisation")
def get_organisation(self, user: User, organisation: Organisation) -> Organisation:
    return organisation
```

The `requires_permission` decorator can be used to enforce access control at the method level. The decorator takes the permission level and the object parameter name as arguments. The permission level is used to check if the user has the required permission to access the object. The `obj_param` argument is used to specify the name of the object parameter in the method signature. If `organisation: Organisation` were renamed to `org: Organisation`, the decorator would be `@requires_permission("view", obj_param="org")`.


## Future Improvements

The current permission system utilises a decorator-based approach with service-level checks, centred around `@requires_permission` and role verification methods. Its strength lies in simplicity and maintainability - the decorator pattern makes permissions explicit, while centralised service logic ensures consistent enforcement across the application. This design fits well with the service-oriented architecture and makes permission checks reusable across different views.

However, the system has notable limitations. Performance can be a concern due to multiple database queries per check with no built-in caching. The hardcoded roles (_Admin_ and _Project Manager_) make it inflexible for custom permission schemes. Some code duplication exists across services, and testing requires some mocking setups.

The current approach works well for basic needs, its simplicity comes at the cost of flexibility and scalability. Future improvements could focus on implementing a policy-based system with better performance characteristics while maintaining the current system's clarity and ease of use, if required.

For example:

```python
class Permission(Enum):
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"
    CREATE = "create"

@dataclass
class OrganisationPolicy:
    user: User
    organisation: Organisation
    
    def get_role(self) -> Optional[str]:
        membership = self.organisation.organisationmembership_set.filter(
            user=self.user
        ).first()
        return membership.role if membership else None
    
    def can(self, permission: Permission) -> bool:
        role = self.get_role()
        if not role:
            return False
            
        permission_matrix = {
            Permission.VIEW: [ROLE_ADMIN, ROLE_PROJECT_MANAGER],
            Permission.EDIT: [ROLE_ADMIN],
            Permission.DELETE: [ROLE_ADMIN],
            Permission.CREATE: [ROLE_ADMIN],
        }
        return role in permission_matrix[permission]

class OrganisationService:
    def get_policy(self, user: User, org: Organisation) -> OrganisationPolicy:
        return OrganisationPolicy(user, org)
        
    def can_view(self, user: User, org: Organisation) -> bool:
        return self.get_policy(user, org).can(Permission.VIEW)
```