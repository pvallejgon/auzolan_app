from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.communities.models import Community, Membership

User = get_user_model()


class RegisterWithCommunityTests(TestCase):
    def setUp(self):
        self.community_a = Community.objects.create(name='Comunidad A')
        self.community_b = Community.objects.create(name='Comunidad B')

    def test_register_creates_membership_in_selected_community(self):
        response = self.client.post(
            '/api/auth/register',
            {
                'email': 'nuevo@example.com',
                'password': 'Pass1234!',
                'display_name': 'Usuario Nuevo',
                'community_id': self.community_b.id,
            },
        )

        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email='nuevo@example.com')
        self.assertTrue(
            Membership.objects.filter(
                user=user,
                community=self.community_b,
                status=Membership.Status.APPROVED,
                role_in_community=Membership.Role.MEMBER,
            ).exists()
        )
        self.assertFalse(Membership.objects.filter(user=user, community=self.community_a).exists())

    def test_register_requires_valid_community_id(self):
        response = self.client.post(
            '/api/auth/register',
            {
                'email': 'otro@example.com',
                'password': 'Pass1234!',
                'display_name': 'Otro Usuario',
                'community_id': 999999,
            },
        )

        self.assertEqual(response.status_code, 400)
