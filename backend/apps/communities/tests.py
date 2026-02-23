from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.communities.models import Community, Membership
from apps.profiles.models import Profile

User = get_user_model()


class CommunityMembersModerationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.community = Community.objects.create(name='Comunidad Moderada')
        self.other_community = Community.objects.create(name='Comunidad Externa')

        self.moderator = User.objects.create_user(
            username='moderator@example.com',
            email='moderator@example.com',
            password='Pass1234!',
        )
        self.member = User.objects.create_user(
            username='member@example.com',
            email='member@example.com',
            password='Pass1234!',
        )
        self.member_two = User.objects.create_user(
            username='member2@example.com',
            email='member2@example.com',
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

        Profile.objects.create(user=self.moderator, display_name='Moderador')
        Profile.objects.create(user=self.member, display_name='Miembro')
        Profile.objects.create(user=self.member_two, display_name='Miembro Dos')
        Profile.objects.create(user=self.outsider, display_name='Externo')

        Membership.objects.create(
            user=self.moderator,
            community=self.community,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MODERATOR,
        )
        Membership.objects.create(
            user=self.member,
            community=self.community,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MEMBER,
        )
        Membership.objects.create(
            user=self.member_two,
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

    def test_community_list_is_public_for_register_flow(self):
        response = self.client.get('/api/communities')
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_list_members(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(f'/api/communities/{self.community.id}/members')
        self.assertEqual(response.status_code, 403)

    def test_moderator_can_list_members_of_community(self):
        self.client.force_authenticate(self.moderator)
        response = self.client.get(f'/api/communities/{self.community.id}/members')

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['count'], 3)
        emails = [row['email'] for row in response.data['results']]
        self.assertIn('member@example.com', emails)

    def test_moderator_can_edit_member_profile_and_status(self):
        self.client.force_authenticate(self.moderator)
        response = self.client.patch(
            f'/api/communities/{self.community.id}/members/{self.member.id}',
            {
                'display_name': 'Miembro Editado',
                'bio': 'Bio moderada',
                'status': Membership.Status.REJECTED,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.profile.display_name, 'Miembro Editado')
        self.assertEqual(self.member.profile.bio, 'Bio moderada')
        membership = Membership.objects.get(user=self.member, community=self.community)
        self.assertEqual(membership.status, Membership.Status.REJECTED)

    def test_moderator_cannot_change_role_in_community(self):
        self.client.force_authenticate(self.moderator)
        response = self.client.patch(
            f'/api/communities/{self.community.id}/members/{self.member.id}',
            {'role_in_community': Membership.Role.MODERATOR},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_superadmin_can_change_role_in_community(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.patch(
            f'/api/communities/{self.community.id}/members/{self.member_two.id}',
            {'role_in_community': Membership.Role.MODERATOR},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        membership = Membership.objects.get(user=self.member_two, community=self.community)
        self.assertEqual(membership.role_in_community, Membership.Role.MODERATOR)
