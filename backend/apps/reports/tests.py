from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.communities.models import Community, Membership
from apps.reports.models import Report
from apps.requests.models import Request

User = get_user_model()


class ReportModerationPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.community_a = Community.objects.create(name='Comunidad A')
        self.community_b = Community.objects.create(name='Comunidad B')

        self.mod_a = User.objects.create_user(
            username='moda@example.com',
            email='moda@example.com',
            password='Pass1234!',
        )
        self.member_a = User.objects.create_user(
            username='membera@example.com',
            email='membera@example.com',
            password='Pass1234!',
        )
        self.member_b = User.objects.create_user(
            username='memberb@example.com',
            email='memberb@example.com',
            password='Pass1234!',
        )
        self.superadmin = User.objects.create_superuser(
            username='super@example.com',
            email='super@example.com',
            password='Pass1234!',
        )

        Membership.objects.create(
            user=self.mod_a,
            community=self.community_a,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MODERATOR,
        )
        Membership.objects.create(
            user=self.member_a,
            community=self.community_a,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MEMBER,
        )
        Membership.objects.create(
            user=self.member_b,
            community=self.community_b,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MEMBER,
        )

        self.request_a = Request.objects.create(
            community=self.community_a,
            created_by_user=self.member_a,
            title='Peticion A',
            description='Descripcion A',
            category='Recados',
        )
        self.request_b = Request.objects.create(
            community=self.community_b,
            created_by_user=self.member_b,
            title='Peticion B',
            description='Descripcion B',
            category='Recados',
        )

        self.report_a = Report.objects.create(
            reporter_user=self.member_a,
            request=self.request_a,
            reason=Report.Reason.OTHER,
            description='Reporte A',
        )
        self.report_b = Report.objects.create(
            reporter_user=self.member_b,
            request=self.request_b,
            reason=Report.Reason.OTHER,
            description='Reporte B',
        )

    def test_member_cannot_list_reports(self):
        self.client.force_authenticate(self.member_a)
        response = self.client.get('/api/reports')
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_update_report_status(self):
        self.client.force_authenticate(self.member_a)
        response = self.client.post(
            f'/api/reports/{self.report_a.id}/status',
            {'status': Report.Status.IN_REVIEW},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_moderator_list_only_own_community_reports(self):
        self.client.force_authenticate(self.mod_a)

        response = self.client.get('/api/reports')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.report_a.id)

    def test_moderator_cannot_list_other_community_reports(self):
        self.client.force_authenticate(self.mod_a)

        response = self.client.get(f'/api/reports?community_id={self.community_b.id}')
        self.assertEqual(response.status_code, 403)

    def test_moderator_get_invalid_community_id_returns_400(self):
        self.client.force_authenticate(self.mod_a)

        response = self.client.get('/api/reports?community_id=abc')
        self.assertEqual(response.status_code, 400)

    def test_moderator_can_update_status_only_in_own_community(self):
        self.client.force_authenticate(self.mod_a)

        allowed = self.client.post(
            f'/api/reports/{self.report_a.id}/status',
            {'status': Report.Status.IN_REVIEW},
            format='json',
        )
        denied = self.client.post(
            f'/api/reports/{self.report_b.id}/status',
            {'status': Report.Status.IN_REVIEW},
            format='json',
        )

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 403)

        self.report_a.refresh_from_db()
        self.assertEqual(self.report_a.status, Report.Status.IN_REVIEW)

    def test_superadmin_can_list_all_reports(self):
        self.client.force_authenticate(self.superadmin)

        response = self.client.get('/api/reports')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_superadmin_can_filter_reports_by_community(self):
        self.client.force_authenticate(self.superadmin)

        response = self.client.get(f'/api/reports?community_id={self.community_b.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.report_b.id)

    def test_superadmin_invalid_community_id_returns_400(self):
        self.client.force_authenticate(self.superadmin)

        response = self.client.get('/api/reports?community_id=abc')
        self.assertEqual(response.status_code, 400)
