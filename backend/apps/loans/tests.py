from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.communities.models import Community, Membership
from apps.loans.models import LoanItem, LoanRequest

User = get_user_model()


class LoansPermissionsAndFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.community = Community.objects.create(name='Comunidad Prestamos')
        self.other_community = Community.objects.create(name='Comunidad Externa')

        self.owner = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='Pass1234!',
        )
        self.borrower = User.objects.create_user(
            username='borrower@example.com',
            email='borrower@example.com',
            password='Pass1234!',
        )
        self.outsider = User.objects.create_user(
            username='outsider@example.com',
            email='outsider@example.com',
            password='Pass1234!',
        )
        self.superadmin = User.objects.create_superuser(
            username='superadmin@example.com',
            email='superadmin@example.com',
            password='Pass1234!',
        )

        Membership.objects.create(
            user=self.owner,
            community=self.community,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MEMBER,
        )
        Membership.objects.create(
            user=self.borrower,
            community=self.community,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MEMBER,
        )
        Membership.objects.create(
            user=self.outsider,
            community=self.other_community,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MEMBER,
        )

        self.item = LoanItem.objects.create(
            community=self.community,
            owner_user=self.owner,
            title='Taladro',
            description='Taladro con brocas',
        )

    def test_non_member_cannot_list_loans(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f'/api/loans?community_id={self.community.id}')
        self.assertEqual(response.status_code, 403)

    def test_member_can_create_loan_item(self):
        self.client.force_authenticate(self.borrower)
        response = self.client.post(
            '/api/loans',
            {
                'community_id': self.community.id,
                'title': 'Escalera plegable',
                'description': 'Ligera y estable',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            LoanItem.objects.filter(
                community=self.community,
                owner_user=self.borrower,
                title='Escalera plegable',
            ).exists()
        )

    def test_member_can_request_available_item(self):
        self.client.force_authenticate(self.borrower)
        response = self.client.post(
            f'/api/loans/{self.item.id}/requests',
            {'message': 'Lo necesito para esta tarde.'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            LoanRequest.objects.filter(
                item=self.item,
                requester_user=self.borrower,
                status=LoanRequest.Status.PENDING,
            ).exists()
        )

    def test_owner_accepts_request_and_item_becomes_loaned(self):
        loan_request = LoanRequest.objects.create(
            item=self.item,
            requester_user=self.borrower,
            message='¿Me lo prestas dos días?',
        )

        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/loans/{self.item.id}/requests/{loan_request.id}/accept')
        self.assertEqual(response.status_code, 200)

        self.item.refresh_from_db()
        loan_request.refresh_from_db()
        self.assertEqual(self.item.status, LoanItem.Status.LOANED)
        self.assertEqual(self.item.borrower_user_id, self.borrower.id)
        self.assertEqual(loan_request.status, LoanRequest.Status.ACCEPTED)

    def test_owner_can_mark_item_as_returned(self):
        self.item.status = LoanItem.Status.LOANED
        self.item.borrower_user = self.borrower
        self.item.save(update_fields=['status', 'borrower_user', 'updated_at'])

        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/loans/{self.item.id}/mark-returned')
        self.assertEqual(response.status_code, 200)

        self.item.refresh_from_db()
        self.assertEqual(self.item.status, LoanItem.Status.AVAILABLE)
        self.assertIsNone(self.item.borrower_user_id)
        self.assertIsNotNone(self.item.returned_at)

    def test_superadmin_can_accept_request_without_membership(self):
        loan_request = LoanRequest.objects.create(
            item=self.item,
            requester_user=self.borrower,
            message='Solicitud para superadmin',
        )
        self.client.force_authenticate(self.superadmin)
        response = self.client.post(f'/api/loans/{self.item.id}/requests/{loan_request.id}/accept')
        self.assertEqual(response.status_code, 200)
