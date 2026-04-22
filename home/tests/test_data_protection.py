from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationMembershipFactory,
    UserFactory,
)
from SORT.test.model_factory.user.constants import PASSWORD

from home.models import DataProtectionEvent
from home.services import data_protection_service


class DataProtectionEventModelTests(SORT.test.test_case.ViewTestCase):
    def _make_event(self):
        return data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.ERASURE,
            subject_user=self.user,
            actioned_by=self.superuser,
            notes="test",
        )

    def test_save_on_existing_instance_raises(self):
        event = self._make_event()
        event.notes = "mutated"
        with self.assertRaises(ValueError):
            event.save()

    def test_delete_raises(self):
        event = self._make_event()
        with self.assertRaises(ValueError):
            event.delete()
        self.assertTrue(
            DataProtectionEvent.objects.filter(pk=event.pk).exists(),
            "Event should remain after a blocked delete()",
        )


class DataProtectionServiceTests(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)

    def test_record_event_persists_expected_fields(self):
        event = data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.EXPORT,
            subject_user=self.user,
            actioned_by=self.staff_user,
            notes="exported",
        )
        self.assertEqual(event.subject_user_id, self.user.pk)
        self.assertEqual(event.subject_identifier, self.user.email)
        self.assertEqual(event.actioned_by, self.staff_user)
        self.assertEqual(event.event_type, "export")

    def test_subject_identifier_falls_back_for_emailless_user(self):
        class _Ghost:
            pk = 99999
            email = ""

        event = data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.ERASURE,
            subject_user=_Ghost(),
            actioned_by=self.staff_user,
        )
        self.assertEqual(event.subject_identifier, "deleted-user-99999")

    def test_list_events_denies_non_staff(self):
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            data_protection_service.list_events(self.user)

    def test_list_events_filters_by_event_type(self):
        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.ERASURE,
            subject_user=self.user,
            actioned_by=self.staff_user,
        )
        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.EXPORT,
            subject_user=self.user,
            actioned_by=self.staff_user,
        )
        events = data_protection_service.list_events(
            self.staff_user, event_type="erasure"
        )
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().event_type, "erasure")


class DataProtectionLogViewTests(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)

    def _login_staff(self):
        self.assertTrue(
            self.client.login(username=self.staff_user.email, password=PASSWORD)
        )

    def test_anonymous_is_redirected(self):
        response = self.client.get("/console/data-protection/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_regular_user_forbidden(self):
        self.login()
        response = self.client.get("/console/data-protection/")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_staff_sees_recorded_event(self):
        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.ERASURE,
            subject_user=self.user,
            actioned_by=self.staff_user,
            notes="test-entry-visible",
        )
        self._login_staff()
        response = self.client.get("/console/data-protection/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.user.email)
        self.assertContains(response, "test-entry-visible")


class RemoveMemberRecordsEventTests(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(is_staff=True)
        self.org = OrganisationFactory()
        self.membership = OrganisationMembershipFactory(
            organisation=self.org, user=self.user
        )

    def test_remove_member_records_restriction_event(self):
        self.assertTrue(
            self.client.login(
                username=self.staff_user.email, password=PASSWORD
            )
        )
        response = self.client.post(
            f"/console/organisations/{self.org.pk}/members/{self.membership.pk}/remove/"
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        events = DataProtectionEvent.objects.filter(
            event_type=DataProtectionEvent.EventType.RESTRICTION,
            subject_user_id=self.user.pk,
        )
        self.assertEqual(events.count(), 1)
        event = events.get()
        self.assertEqual(event.actioned_by, self.staff_user)
        self.assertIn(self.org.name, event.notes)
