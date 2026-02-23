from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Community, Membership
from apps.communities.serializers import (
    CommunityMemberSerializer,
    CommunityMemberUpdateSerializer,
    CommunitySerializer,
)
from apps.core.pagination import StandardResultsPagination
from apps.core.permissions import is_moderator_in_community, is_superadmin
from apps.profiles.models import Profile


def ensure_base_communities():
    Community.objects.get_or_create(
        name='Obanos',
        defaults={'description': 'Comunidad local de Obanos para el MVP.'},
    )
    Community.objects.get_or_create(
        name='Com. Vecinos',
        defaults={'description': 'Comunidad de vecinos para pruebas del MVP.'},
    )


def can_manage_community(user, community_id):
    return is_superadmin(user) or is_moderator_in_community(user, community_id)


def get_default_display_name(user):
    if user.email and '@' in user.email:
        return user.email.split('@', 1)[0]
    return f'Usuario {user.id}'


class CommunityListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary='Listar comunidades',
        description='Devuelve la lista de comunidades disponibles. En la demo incluye Obanos y Com. Vecinos.',
        responses={200: CommunitySerializer(many=True)},
    )
    def get(self, request):
        ensure_base_communities()
        communities = Community.objects.all().order_by('id')
        serializer = CommunitySerializer(communities, many=True)
        return Response(serializer.data)


class JoinCommunityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Unirse a una comunidad',
        description='Crea la membresía del usuario en la comunidad. En el MVP queda aprobada automáticamente.',
    )
    def post(self, request, community_id):
        community = get_object_or_404(Community, id=community_id)
        membership, _ = Membership.objects.get_or_create(
            user=request.user,
            community=community,
            defaults={
                'status': Membership.Status.APPROVED,
                'role_in_community': Membership.Role.MEMBER,
                'joined_at': timezone.now(),
            },
        )
        return Response(
            {
                'community_id': membership.community_id,
                'status': membership.status,
            },
            status=status.HTTP_200_OK,
        )


class CommunityMembersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar miembros de una comunidad',
        description='Solo moderador de la comunidad o superadmin.',
        parameters=[
            OpenApiParameter(name='page', description='Página', required=False, type=int),
            OpenApiParameter(name='page_size', description='Tamaño de página', required=False, type=int),
        ],
        responses={200: CommunityMemberSerializer(many=True)},
    )
    def get(self, request, community_id):
        community = get_object_or_404(Community, id=community_id)
        if not can_manage_community(request.user, community.id):
            return Response({'detail': 'No tienes permisos de moderación en esta comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        memberships = (
            Membership.objects.filter(community=community)
            .select_related('user', 'user__profile')
            .order_by('role_in_community', 'user__email')
        )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(memberships, request)
        serializer = CommunityMemberSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CommunityMemberUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Actualizar miembro de comunidad',
        description='Moderador o superadmin pueden actualizar datos de usuario y membresía.',
        request=CommunityMemberUpdateSerializer,
        responses={200: CommunityMemberSerializer},
    )
    def patch(self, request, community_id, user_id):
        community = get_object_or_404(Community, id=community_id)
        if not can_manage_community(request.user, community.id):
            return Response({'detail': 'No tienes permisos de moderación en esta comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        membership = get_object_or_404(
            Membership.objects.select_related('user', 'user__profile'),
            community=community,
            user_id=user_id,
        )
        serializer = CommunityMemberUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        actor_is_superadmin = is_superadmin(request.user)

        if not actor_is_superadmin and membership.user.is_superuser:
            return Response({'detail': 'No puedes editar un superadmin.'}, status=status.HTTP_403_FORBIDDEN)

        if 'role_in_community' in validated and not actor_is_superadmin:
            return Response({'detail': 'Solo superadmin puede cambiar el rol en comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        profile_fields_to_update = []
        profile = None
        if 'display_name' in validated or 'bio' in validated:
            profile, _ = Profile.objects.get_or_create(
                user=membership.user,
                defaults={'display_name': get_default_display_name(membership.user)},
            )

            if 'display_name' in validated:
                profile.display_name = validated['display_name']
                profile_fields_to_update.append('display_name')
            if 'bio' in validated:
                profile.bio = validated['bio']
                profile_fields_to_update.append('bio')

            if profile_fields_to_update:
                profile.save(update_fields=profile_fields_to_update + ['updated_at'])

        membership_fields_to_update = []
        if 'status' in validated:
            membership.status = validated['status']
            membership_fields_to_update.append('status')
        if 'role_in_community' in validated and actor_is_superadmin:
            membership.role_in_community = validated['role_in_community']
            membership_fields_to_update.append('role_in_community')

        if membership_fields_to_update:
            membership.save(update_fields=membership_fields_to_update + ['updated_at'])

        membership.refresh_from_db()
        return Response(CommunityMemberSerializer(membership).data, status=status.HTTP_200_OK)
