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
        self.community = Community.objects.create(name='Comunidad Demo')
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
        self.community = Community.objects.create(name='Comunidad Demo')
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
