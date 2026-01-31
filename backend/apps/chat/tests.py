from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.communities.models import Community, Membership
from apps.requests.models import Request, VolunteerOffer
from apps.chat.models import Conversation

User = get_user_model()


class ChatPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.community = Community.objects.create(name='Comunidad Demo')
        self.creator = User.objects.create_user(username='creator3@example.com', email='creator3@example.com', password='Pass1234!')
        self.volunteer = User.objects.create_user(username='vol3@example.com', email='vol3@example.com', password='Pass1234!')
        self.other = User.objects.create_user(username='other3@example.com', email='other3@example.com', password='Pass1234!')
        Membership.objects.create(user=self.creator, community=self.community, status=Membership.Status.APPROVED)
        Membership.objects.create(user=self.volunteer, community=self.community, status=Membership.Status.APPROVED)
        Membership.objects.create(user=self.other, community=self.community, status=Membership.Status.APPROVED)
        self.request = Request.objects.create(
            community=self.community,
            created_by_user=self.creator,
            title='Test chat',
            description='Test chat',
            category='general',
            status=Request.Status.IN_PROGRESS,
        )
        offer = VolunteerOffer.objects.create(
            request=self.request,
            volunteer_user=self.volunteer,
            status=VolunteerOffer.Status.ACCEPTED,
        )
        self.request.accepted_offer = offer
        self.request.save(update_fields=['accepted_offer'])
        self.conversation = Conversation.objects.create(request=self.request)

    def test_non_participant_cannot_read_messages(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(f'/api/conversations/{self.conversation.id}/messages')
        self.assertEqual(response.status_code, 403)
