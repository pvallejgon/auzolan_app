from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.models import Profile
from apps.profiles.serializers import ProfileUpdateSerializer


def default_display_name_for_user(user):
    if user.email and '@' in user.email:
        return user.email.split('@', 1)[0]
    return f'Usuario {user.id}'


class MeProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Perfil propio',
        description='Devuelve la información editable del usuario autenticado.',
    )
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={'display_name': default_display_name_for_user(request.user)},
        )

        return Response(
            {
                'id': request.user.id,
                'email': request.user.email,
                'display_name': profile.display_name,
                'bio': profile.bio,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary='Editar perfil propio',
        description='Permite actualizar display_name y bio. El email es solo lectura.',
        request=ProfileUpdateSerializer,
    )
    def patch(self, request):
        if 'email' in request.data:
            return Response({'detail': 'El email no se puede editar.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={'display_name': default_display_name_for_user(request.user)},
        )

        fields_to_update = []
        if 'display_name' in validated:
            profile.display_name = validated['display_name']
            fields_to_update.append('display_name')
        if 'bio' in validated:
            profile.bio = validated['bio']
            fields_to_update.append('bio')

        if fields_to_update:
            profile.save(update_fields=fields_to_update + ['updated_at'])

        return Response(
            {
                'id': request.user.id,
                'email': request.user.email,
                'display_name': profile.display_name,
                'bio': profile.bio,
            },
            status=status.HTTP_200_OK,
        )
