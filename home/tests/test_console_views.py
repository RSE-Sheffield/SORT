from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory import OrganisationFactory, OrganisationMembershipFactory, ProjectFactory, SurveyFactory, \
    SuperUserFactory, UserFactory
from SORT.test.model_factory.user.constants import PASSWORD


class ConsoleViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)

    def login_staff(self):
        self.assertTrue(
            self.client.login(username=self.staff_user.email, password=PASSWORD),
            "Staff authentication failed",
        )

    def test_console_dashboard_accessible_to_staff(self):
        """Staff users can access the console dashboard."""
        self.login_staff()
        response = self.client.get("/console/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_dashboard_redirects_anonymous(self):
        """Anonymous users are redirected away from the console dashboard."""
        response = self.client.get("/console/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_dashboard_forbidden_for_regular_users(self):
        """Regular (non-staff) users cannot access the console dashboard."""
        self.login()
        response = self.client.get("/console/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_organisations_accessible_to_staff(self):
        """Staff users can access the organisations list."""
        self.login_staff()
        response = self.client.get("/console/organisations/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_organisations_redirects_anonymous(self):
        """Anonymous users are redirected away from the organisations list."""
        response = self.client.get("/console/organisations/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_organisations_forbidden_for_regular_users(self):
        """Regular users cannot access the organisations list."""
        self.login()
        response = self.client.get("/console/organisations/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_users_accessible_to_staff(self):
        """Staff users can access the users list."""
        self.login_staff()
        response = self.client.get("/console/users/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_users_redirects_anonymous(self):
        """Anonymous users are redirected away from the users list."""
        response = self.client.get("/console/users/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_users_forbidden_for_regular_users(self):
        """Regular users cannot access the users list."""
        self.login()
        response = self.client.get("/console/users/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_surveys_accessible_to_staff(self):
        """Staff users can access the surveys list."""
        self.login_staff()
        response = self.client.get("/console/surveys/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_surveys_redirects_anonymous(self):
        """Anonymous users are redirected away from the surveys list."""
        response = self.client.get("/console/surveys/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_surveys_forbidden_for_regular_users(self):
        """Regular users cannot access the surveys list."""
        self.login()
        response = self.client.get("/console/surveys/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_organisation_detail_accessible_to_staff(self):
        """Staff users can access the organisation detail view."""
        org = OrganisationFactory()
        self.login_staff()
        response = self.client.get(f"/console/organisations/{org.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_organisation_detail_redirects_anonymous(self):
        """Anonymous users are redirected away from the organisation detail view."""
        org = OrganisationFactory()
        response = self.client.get(f"/console/organisations/{org.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_organisation_detail_forbidden_for_regular_users(self):
        """Regular users cannot access the organisation detail view."""
        org = OrganisationFactory()
        self.login()
        response = self.client.get(f"/console/organisations/{org.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_projects_accessible_to_staff(self):
        """Staff users can access the projects list."""
        self.login_staff()
        response = self.client.get("/console/projects/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_projects_redirects_anonymous(self):
        """Anonymous users are redirected away from the projects list."""
        response = self.client.get("/console/projects/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_projects_forbidden_for_regular_users(self):
        """Regular users cannot access the projects list."""
        self.login()
        response = self.client.get("/console/projects/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_project_detail_accessible_to_staff(self):
        """Staff users can access the project detail view."""
        project = ProjectFactory()
        self.login_staff()
        response = self.client.get(f"/console/projects/{project.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_project_detail_redirects_anonymous(self):
        """Anonymous users are redirected away from the project detail view."""
        project = ProjectFactory()
        response = self.client.get(f"/console/projects/{project.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_project_detail_forbidden_for_regular_users(self):
        """Regular users cannot access the project detail view."""
        project = ProjectFactory()
        self.login()
        response = self.client.get(f"/console/projects/{project.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_survey_detail_accessible_to_staff(self):
        """Staff users can access the survey detail view."""
        survey = SurveyFactory()
        self.login_staff()
        response = self.client.get(f"/console/surveys/{survey.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_survey_detail_redirects_anonymous(self):
        """Anonymous users are redirected away from the survey detail view."""
        survey = SurveyFactory()
        response = self.client.get(f"/console/surveys/{survey.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_survey_detail_forbidden_for_regular_users(self):
        """Regular users cannot access the survey detail view."""
        survey = SurveyFactory()
        self.login()
        response = self.client.get(f"/console/surveys/{survey.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_user_detail_accessible_to_staff(self):
        """Staff users can access the user detail view."""
        user = UserFactory()
        self.login_staff()
        response = self.client.get(f"/console/users/{user.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_user_detail_redirects_anonymous(self):
        """Anonymous users are redirected away from the user detail view."""
        user = UserFactory()
        response = self.client.get(f"/console/users/{user.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_user_detail_forbidden_for_regular_users(self):
        """Regular users cannot access the user detail view."""
        user = UserFactory()
        self.login()
        response = self.client.get(f"/console/users/{user.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_remove_member_get_accessible_to_staff(self):
        """Staff users can access the remove member confirmation page."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(organisation=org)
        self.login_staff()
        response = self.client.get(f"/console/organisations/{org.pk}/members/{membership.pk}/remove/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_remove_member_get_redirects_anonymous(self):
        """Anonymous users are redirected away from the remove member page."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(organisation=org)
        response = self.client.get(f"/console/organisations/{org.pk}/members/{membership.pk}/remove/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_remove_member_get_forbidden_for_regular_users(self):
        """Regular users cannot access the remove member confirmation page."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(organisation=org)
        self.login()
        response = self.client.get(f"/console/organisations/{org.pk}/members/{membership.pk}/remove/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_remove_member_post_removes_membership(self):
        """Staff users can POST to remove a member from an organisation."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(organisation=org)
        membership_pk = membership.pk
        self.login_staff()
        response = self.client.post(f"/console/organisations/{org.pk}/members/{membership_pk}/remove/")
        self.assertRedirects(response, f"/console/organisations/{org.pk}/")
        from home.models import OrganisationMembership
        self.assertFalse(OrganisationMembership.objects.filter(pk=membership_pk).exists())

    # -- Suspend / unsuspend user --------------------------------------------

    def test_console_suspend_user_get_accessible_to_staff(self):
        """Staff users can access the suspend confirmation page."""
        user = UserFactory()
        self.login_staff()
        response = self.client.get(f"/console/users/{user.pk}/suspend/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_console_suspend_user_get_redirects_anonymous(self):
        """Anonymous users are redirected away from the suspend page."""
        user = UserFactory()
        response = self.client.get(f"/console/users/{user.pk}/suspend/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_console_suspend_user_get_forbidden_for_regular_users(self):
        """Regular users cannot access the suspend page."""
        user = UserFactory()
        self.login()
        response = self.client.get(f"/console/users/{user.pk}/suspend/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_console_suspend_user_post_suspends_without_deleting_data(self):
        """POSTing to suspend sets is_active=False, leaving data intact."""
        user = UserFactory()
        membership = OrganisationMembershipFactory(user=user, organisation=OrganisationFactory())
        self.login_staff()
        response = self.client.post(f"/console/users/{user.pk}/suspend/")
        self.assertRedirects(response, f"/console/users/{user.pk}/")
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        # No cascade: the user and their memberships still exist.
        self.assertTrue(UserFactory._meta.model.objects.filter(pk=user.pk).exists())
        from home.models import OrganisationMembership
        self.assertTrue(OrganisationMembership.objects.filter(pk=membership.pk).exists())

    def test_console_suspend_user_post_unsuspends(self):
        """POSTing to unsuspend restores is_active=True."""
        user = UserFactory(is_active=False)
        self.login_staff()
        response = self.client.post(f"/console/users/{user.pk}/unsuspend/")
        self.assertRedirects(response, f"/console/users/{user.pk}/")
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_console_suspend_self_forbidden(self):
        """Staff cannot suspend their own account."""
        self.login_staff()
        response = self.client.post(f"/console/users/{self.staff_user.pk}/suspend/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.staff_user.refresh_from_db()
        self.assertTrue(self.staff_user.is_active)

    def test_console_suspend_superuser_forbidden(self):
        """Superuser accounts cannot be suspended."""
        target = SuperUserFactory()
        self.login_staff()
        response = self.client.post(f"/console/users/{target.pk}/suspend/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        target.refresh_from_db()
        self.assertTrue(target.is_active)

    def test_console_user_list_shows_suspended_users(self):
        """Suspended users remain visible in the console user list."""
        suspended = UserFactory(is_active=False)
        self.login_staff()
        response = self.client.get("/console/users/")
        self.assertContains(response, suspended.email)
        self.assertContains(response, "Suspended")
