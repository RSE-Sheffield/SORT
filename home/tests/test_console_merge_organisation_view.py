from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationMembershipFactory,
    ProjectFactory,
    UserFactory,
)
from SORT.test.model_factory.user.constants import PASSWORD

from home.models import Organisation


class ConsoleMergeOrganisationViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)
        self.source = OrganisationFactory()
        self.target = OrganisationFactory()

    def login_staff(self):
        self.assertTrue(
            self.client.login(username=self.staff_user.email, password=PASSWORD),
            "Staff authentication failed",
        )

    def test_get_redirects_anonymous(self):
        response = self.client.get(f"/console/organisations/{self.source.pk}/merge/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_get_forbidden_for_regular_users(self):
        self.login()
        response = self.client.get(f"/console/organisations/{self.source.pk}/merge/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_without_target_shows_picker_only(self):
        self.login_staff()
        response = self.client.get(f"/console/organisations/{self.source.pk}/merge/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn("plan", response.context)

    def test_get_with_valid_target_shows_preview(self):
        project = ProjectFactory(organisation=self.source)
        membership = OrganisationMembershipFactory(organisation=self.source)
        self.login_staff()
        response = self.client.get(
            f"/console/organisations/{self.source.pk}/merge/",
            {"target": self.target.pk},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        plan = response.context["plan"]
        self.assertIn(project, plan.projects)
        self.assertIn(membership, plan.memberships_to_move)

    def test_get_with_self_target_shows_no_preview(self):
        self.login_staff()
        response = self.client.get(
            f"/console/organisations/{self.source.pk}/merge/",
            {"target": self.source.pk},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn("plan", response.context)

    def test_get_with_invalid_target_shows_no_preview(self):
        self.login_staff()
        response = self.client.get(
            f"/console/organisations/{self.source.pk}/merge/",
            {"target": 999999},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn("plan", response.context)

    def test_post_merges_organisations(self):
        project = ProjectFactory(organisation=self.source)
        membership = OrganisationMembershipFactory(organisation=self.source)
        source_pk = self.source.pk
        target_pk = self.target.pk
        self.login_staff()

        response = self.client.post(
            f"/console/organisations/{source_pk}/merge/",
            {"target_id": target_pk},
        )

        self.assertRedirects(response, f"/console/organisations/{target_pk}/")
        self.assertFalse(Organisation.objects.filter(pk=source_pk).exists())
        project.refresh_from_db()
        self.assertEqual(project.organisation_id, target_pk)
        membership.refresh_from_db()
        self.assertEqual(membership.organisation_id, target_pk)

    def test_post_rejects_self_merge_without_deleting(self):
        source_pk = self.source.pk
        self.login_staff()

        response = self.client.post(
            f"/console/organisations/{source_pk}/merge/",
            {"target_id": source_pk},
        )

        self.assertRedirects(
            response, f"/console/organisations/{source_pk}/merge/"
        )
        self.assertTrue(Organisation.objects.filter(pk=source_pk).exists())
