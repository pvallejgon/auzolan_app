from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.profiles.models import Profile

User = get_user_model()


class MeProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='profile@example.com',
            email='profile@example.com',
            password='Pass1234!',
        )
        Profile.objects.create(user=self.user, display_name='Perfil Inicial', bio='Bio inicial')

    def test_get_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/profile')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'profile@example.com')
        self.assertEqual(response.data['display_name'], 'Perfil Inicial')
        self.assertEqual(response.data['bio'], 'Bio inicial')

    def test_patch_profile_updates_display_name_and_bio(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            '/api/profile',
            {
                'display_name': 'Perfil Editado',
                'bio': 'Bio editada',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, 'Perfil Editado')
        self.assertEqual(self.user.profile.bio, 'Bio editada')

    def test_patch_profile_rejects_email_changes(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            '/api/profile',
            {'email': 'nuevo@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'profile@example.com')
