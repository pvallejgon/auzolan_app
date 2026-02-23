from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.communities.models import Community, Membership
from apps.requests.models import Request, VolunteerOffer
from apps.chat.models import Conversation

User = get_user_model()


class RequestPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.community = Community.objects.create(name='Obanos')
        self.creator = User.objects.create_user(username='creator@example.com', email='creator@example.com', password='Pass1234!')
        Membership.objects.create(user=self.creator, community=self.community, status=Membership.Status.APPROVED)
        self.request = Request.objects.create(
            community=self.community,
            created_by_user=self.creator,
            title='Test',
            description='Test',
            category='general',
        )
        self.other = User.objects.create_user(username='other@example.com', email='other@example.com', password='Pass1234!')

    def test_non_member_cannot_list_requests(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(f'/api/requests?community_id={self.community.id}')
        self.assertEqual(response.status_code, 403)


class AcceptOfferFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.community = Community.objects.create(name='Obanos')
        self.creator = User.objects.create_user(username='creator2@example.com', email='creator2@example.com', password='Pass1234!')
        Membership.objects.create(user=self.creator, community=self.community, status=Membership.Status.APPROVED)
        self.vol1 = User.objects.create_user(username='vol1@example.com', email='vol1@example.com', password='Pass1234!')
        self.vol2 = User.objects.create_user(username='vol2@example.com', email='vol2@example.com', password='Pass1234!')
        Membership.objects.create(user=self.vol1, community=self.community, status=Membership.Status.APPROVED)
        Membership.objects.create(user=self.vol2, community=self.community, status=Membership.Status.APPROVED)
        self.request = Request.objects.create(
            community=self.community,
            created_by_user=self.creator,
            title='Test2',
            description='Test2',
            category='general',
        )
        self.offer1 = VolunteerOffer.objects.create(request=self.request, volunteer_user=self.vol1)
        self.offer2 = VolunteerOffer.objects.create(request=self.request, volunteer_user=self.vol2)

    def test_accept_offer_transitions(self):
        self.client.force_authenticate(self.creator)
        response = self.client.post(f'/api/requests/{self.request.id}/accept-offer/{self.offer1.id}')
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.offer1.refresh_from_db()
        self.offer2.refresh_from_db()
        self.assertEqual(self.request.status, Request.Status.IN_PROGRESS)
        self.assertEqual(self.request.accepted_offer_id, self.offer1.id)
        self.assertEqual(self.offer1.status, VolunteerOffer.Status.ACCEPTED)
        self.assertEqual(self.offer2.status, VolunteerOffer.Status.REJECTED)
        self.assertTrue(Conversation.objects.filter(request=self.request).exists())


class RequestModerationEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.community_a = Community.objects.create(name='Comunidad A')
        self.community_b = Community.objects.create(name='Comunidad B')

        self.moderator_a = User.objects.create_user(
            username='moderator.a@example.com',
            email='moderator.a@example.com',
            password='Pass1234!',
        )
        self.member_a = User.objects.create_user(
            username='member.a@example.com',
            email='member.a@example.com',
            password='Pass1234!',
        )
        self.member_b = User.objects.create_user(
            username='member.b@example.com',
            email='member.b@example.com',
            password='Pass1234!',
        )
        self.superadmin = User.objects.create_superuser(
            username='super@example.com',
            email='super@example.com',
            password='Pass1234!',
        )

        Membership.objects.create(
            user=self.moderator_a,
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

    def test_member_cannot_use_moderation_close_endpoint(self):
        self.client.force_authenticate(self.member_a)
        response = self.client.post(
            f'/api/moderation/requests/{self.request_a.id}/close',
            {'status': Request.Status.CANCELLED},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_moderator_can_close_request_in_own_community(self):
        self.client.force_authenticate(self.moderator_a)
        response = self.client.post(
            f'/api/moderation/requests/{self.request_a.id}/close',
            {'status': Request.Status.CANCELLED},
            format='json',
        )
        self.assertEqual(response.status_code, 200)

        self.request_a.refresh_from_db()
        self.assertEqual(self.request_a.status, Request.Status.CANCELLED)

    def test_moderator_cannot_close_request_in_other_community(self):
        self.client.force_authenticate(self.moderator_a)
        response = self.client.post(
            f'/api/moderation/requests/{self.request_b.id}/close',
            {'status': Request.Status.CANCELLED},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_superadmin_can_close_request_in_any_community(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.post(
            f'/api/moderation/requests/{self.request_b.id}/close',
            {'status': Request.Status.CANCELLED},
            format='json',
        )
        self.assertEqual(response.status_code, 200)

        self.request_b.refresh_from_db()
        self.assertEqual(self.request_b.status, Request.Status.CANCELLED)

    def test_moderator_can_delete_request_in_own_community(self):
        self.client.force_authenticate(self.moderator_a)
        response = self.client.delete(f'/api/moderation/requests/{self.request_a.id}')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Request.objects.filter(id=self.request_a.id).exists())

    def test_superadmin_can_delete_request_in_any_community(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.delete(f'/api/moderation/requests/{self.request_b.id}')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Request.objects.filter(id=self.request_b.id).exists())
