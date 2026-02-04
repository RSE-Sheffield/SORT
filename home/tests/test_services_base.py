"""
Unit tests for home.services.base module
"""

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from SORT.test.model_factory import OrganisationFactory, ProjectFactory, UserFactory
from home.services.base import BasePermissionService, requires_permission


class MockService(BasePermissionService):
    """Mock service for testing permission decorators"""

    def can_view(self, user, instance):
        return user.username == "viewer" or user.is_superuser

    def can_edit(self, user, instance):
        return user.username == "editor" or user.is_superuser

    def can_delete(self, user, instance):
        return user.username == "deleter" or user.is_superuser

    def can_create(self, user, instance):
        return user.username == "creator" or user.is_superuser

    @requires_permission("view", "proj")
    def get_project(self, user, proj):
        return proj

    @requires_permission("edit", "proj")
    def update_project(self, user, proj, data):
        return {"updated": True}

    @requires_permission("delete", "proj")
    def delete_project(self, user, proj):
        return {"deleted": True}

    @requires_permission("create", "org")
    def create_project(self, user, org):
        return {"created": True}


class RequiresPermissionDecoratorTestCase(TestCase):
    """Tests for the requires_permission decorator"""

    def setUp(self):
        self.service = MockService()
        self.project = ProjectFactory()
        self.organisation = OrganisationFactory()

        self.viewer = UserFactory(username="viewer")
        self.editor = UserFactory(username="editor")
        self.deleter = UserFactory(username="deleter")
        self.creator = UserFactory(username="creator")
        self.unauthorized = UserFactory(username="unauthorized")
        self.superuser = UserFactory(username="superuser", is_superuser=True)

    def test_requires_permission_view_authorized(self):
        """Test that authorized user can access view-protected method"""
        result = self.service.get_project(self.viewer, proj=self.project)
        self.assertEqual(result, self.project)

    def test_requires_permission_view_unauthorized(self):
        """Test that unauthorized user cannot access view-protected method"""
        with self.assertRaises(PermissionDenied) as context:
            self.service.get_project(self.unauthorized, proj=self.project)

        self.assertIn("does not have view permission", str(context.exception))

    def test_requires_permission_edit_authorized(self):
        """Test that authorized user can access edit-protected method"""
        result = self.service.update_project(self.editor, proj=self.project, data={})
        self.assertEqual(result, {"updated": True})

    def test_requires_permission_edit_unauthorized(self):
        """Test that unauthorized user cannot access edit-protected method"""
        with self.assertRaises(PermissionDenied) as context:
            self.service.update_project(self.unauthorized, proj=self.project, data={})

        self.assertIn("does not have edit permission", str(context.exception))

    def test_requires_permission_delete_authorized(self):
        """Test that authorized user can access delete-protected method"""
        result = self.service.delete_project(self.deleter, proj=self.project)
        self.assertEqual(result, {"deleted": True})

    def test_requires_permission_delete_unauthorized(self):
        """Test that unauthorized user cannot access delete-protected method"""
        with self.assertRaises(PermissionDenied) as context:
            self.service.delete_project(self.unauthorized, proj=self.project)

        self.assertIn("does not have delete permission", str(context.exception))

    def test_requires_permission_create_authorized(self):
        """Test that authorized user can access create-protected method"""
        result = self.service.create_project(self.creator, org=self.organisation)
        self.assertEqual(result, {"created": True})

    def test_requires_permission_create_unauthorized(self):
        """Test that unauthorized user cannot access create-protected method"""
        with self.assertRaises(PermissionDenied) as context:
            self.service.create_project(self.unauthorized, org=self.organisation)

        self.assertIn("does not have create permission", str(context.exception))

    def test_superuser_has_all_permissions(self):
        """Test that superuser can access all protected methods"""
        self.assertEqual(
            self.service.get_project(self.superuser, proj=self.project), self.project
        )
        self.assertEqual(
            self.service.update_project(self.superuser, proj=self.project, data={}),
            {"updated": True},
        )
        self.assertEqual(
            self.service.delete_project(self.superuser, proj=self.project),
            {"deleted": True},
        )
        self.assertEqual(
            self.service.create_project(self.superuser, org=self.organisation),
            {"created": True},
        )

    def test_permission_error_message_includes_user(self):
        """Test that permission error includes username"""
        with self.assertRaises(PermissionDenied) as context:
            self.service.get_project(self.unauthorized, proj=self.project)

        self.assertIn("unauthorized", str(context.exception))

    def test_permission_error_message_includes_object(self):
        """Test that permission error includes object representation"""
        with self.assertRaises(PermissionDenied) as context:
            self.service.get_project(self.unauthorized, proj=self.project)

        error_message = str(context.exception)
        self.assertIn("Project", error_message)

    def test_decorator_with_positional_argument(self):
        """Test decorator works with positional arguments"""

        class ServiceWithPositional(MockService):
            @requires_permission("view", "proj")
            def method_with_positional(self, user, proj):
                return proj

        service = ServiceWithPositional()
        result = service.method_with_positional(self.viewer, self.project)
        self.assertEqual(result, self.project)

    def test_decorator_missing_object_parameter(self):
        """Test decorator raises error when object parameter is missing"""

        class ServiceWithMissingParam(MockService):
            @requires_permission("view", "missing_param")
            def method_missing_param(self, user, proj):
                return proj

        service = ServiceWithMissingParam()

        with self.assertRaises(ValueError) as context:
            service.method_missing_param(self.viewer, proj=self.project)

        self.assertIn("Could not find object parameter", str(context.exception))

    def test_decorator_with_empty_obj_param(self):
        """Test decorator raises error with empty obj_param"""

        with self.assertRaises(ValueError):

            @requires_permission("view", "")
            def dummy_function(service, user, proj):
                pass

            dummy_function(self.service, self.viewer, proj=self.project)

    def test_decorator_with_nonexistent_permission_method(self):
        """Test decorator raises error when permission method doesn't exist"""

        class ServiceMissingPermission:
            @requires_permission("unknown_permission", "proj")
            def method_with_unknown_permission(self, user, proj):
                return proj

        service = ServiceMissingPermission()

        with self.assertRaises(AttributeError):
            service.method_with_unknown_permission(self.viewer, proj=self.project)

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves the original function name"""
        self.assertEqual(self.service.get_project.__name__, "get_project")
        self.assertEqual(self.service.update_project.__name__, "update_project")

    def test_decorator_with_additional_kwargs(self):
        """Test decorator works with additional keyword arguments"""
        result = self.service.update_project(
            self.editor, proj=self.project, data={"key": "value"}
        )
        self.assertEqual(result, {"updated": True})

    def test_permission_check_method_is_called(self):
        """Test that the appropriate permission check method is called"""
        call_count = {"view": 0, "edit": 0, "delete": 0, "create": 0}

        class TrackingService(MockService):
            def can_view(self, user, instance):
                call_count["view"] += 1
                return super().can_view(user, instance)

            def can_edit(self, user, instance):
                call_count["edit"] += 1
                return super().can_edit(user, instance)

        service = TrackingService()

        service.get_project(self.viewer, proj=self.project)
        self.assertEqual(call_count["view"], 1)

        service.update_project(self.editor, proj=self.project, data={})
        self.assertEqual(call_count["edit"], 1)


class BasePermissionServiceTestCase(TestCase):
    """Tests for BasePermissionService class"""

    def setUp(self):
        self.service = BasePermissionService()
        self.user = UserFactory()
        self.obj = ProjectFactory()

    def test_can_view_not_implemented(self):
        """Test that can_view raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.service.can_view(self.user, self.obj)

    def test_can_edit_not_implemented(self):
        """Test that can_edit raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.service.can_edit(self.user, self.obj)

    def test_can_delete_not_implemented(self):
        """Test that can_delete raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.service.can_delete(self.user, self.obj)

    def test_can_create_not_implemented(self):
        """Test that can_create raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.service.can_create(self.user, self.obj)

    def test_base_service_is_abstract(self):
        """Test that BasePermissionService requires implementation of methods"""
        # All four methods should raise NotImplementedError
        methods = ["can_view", "can_edit", "can_delete", "can_create"]

        for method_name in methods:
            method = getattr(self.service, method_name)
            with self.assertRaises(NotImplementedError):
                method(self.user, self.obj)

    def test_subclass_must_implement_methods(self):
        """Test that subclasses must implement permission methods"""

        class IncompleteService(BasePermissionService):
            def can_view(self, user, instance):
                return True

            # Missing other methods

        service = IncompleteService()

        # can_view is implemented
        self.assertTrue(service.can_view(self.user, self.obj))

        # Others should raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            service.can_edit(self.user, self.obj)

        with self.assertRaises(NotImplementedError):
            service.can_delete(self.user, self.obj)

        with self.assertRaises(NotImplementedError):
            service.can_create(self.user, self.obj)


class PermissionDecoratorEdgeCasesTestCase(TestCase):
    """Edge case tests for permission decorator"""

    def setUp(self):
        self.service = MockService()
        self.project = ProjectFactory()
        self.viewer = UserFactory(username="viewer")

    def test_decorator_with_none_user(self):
        """Test decorator behavior with None user"""

        class ServiceAllowingNone(MockService):
            def can_view(self, user, instance):
                return user is None

            @requires_permission("view", "proj")
            def get_with_none(self, user, proj):
                return proj

        service = ServiceAllowingNone()

        # Should work with None if permission check allows it
        result = service.get_with_none(None, proj=self.project)
        self.assertEqual(result, self.project)

    def test_decorator_with_none_object(self):
        """Test decorator behavior when object is None"""

        class ServiceHandlingNone(MockService):
            def can_view(self, user, instance):
                return instance is None

            @requires_permission("view", "proj")
            def get_with_none_obj(self, user, proj):
                return "handled"

        service = ServiceHandlingNone()

        # Should work if can_view handles None
        result = service.get_with_none_obj(self.viewer, proj=None)
        self.assertEqual(result, "handled")

    def test_multiple_decorators_on_same_method(self):
        """Test that multiple permission decorators can be stacked"""

        class MultiDecoratorService(MockService):
            @requires_permission("view", "proj")
            @requires_permission("edit", "proj")
            def multi_permission_method(self, user, proj):
                return proj

        service = MultiDecoratorService()

        # User needs both view and edit permissions
        viewer_only = UserFactory(username="viewer")
        editor_viewer = UserFactory(username="editor")

        # Viewer doesn't have edit permission
        with self.assertRaises(PermissionDenied):
            service.multi_permission_method(viewer_only, proj=self.project)

        # Editor has edit permission and view will be checked first
        # This will fail at view check since editor isn't a viewer
        with self.assertRaises(PermissionDenied):
            service.multi_permission_method(editor_viewer, proj=self.project)
