from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.communities.models import Community, Membership
from apps.communities.serializers import CommunitySerializer


class CommunityListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar comunidades',
        description='Devuelve la lista de comunidades disponibles. En el MVP devuelve la Comunidad Demo.',
        responses={200: CommunitySerializer(many=True)},
    )
    def get(self, request):
        if not Community.objects.exists():
            Community.objects.get_or_create(
                name='Comunidad Demo',
                defaults={'description': 'Comunidad por defecto para el MVP.'},
            )
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
