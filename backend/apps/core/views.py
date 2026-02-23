from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.communities.models import Community, Membership
from apps.core.serializers import RegisterSerializer, CustomTokenObtainPairSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary='Registro de usuario',
        description='Crea un usuario, su perfil y la membresía aprobada en la comunidad seleccionada.',
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description='Usuario creado',
                response={
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'email': {'type': 'string'},
                        'display_name': {'type': 'string'},
                    },
                },
            )
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = user.profile
        return Response(
            {
                'id': user.id,
                'email': user.email,
                'display_name': profile.display_name,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    summary='Obtener tokens JWT',
    description='Devuelve access y refresh token usando email y contraseña.',
    responses={200: OpenApiResponse(description='Tokens generados')},
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    summary='Refrescar token JWT',
    description='Devuelve un nuevo access token a partir de un refresh token válido.',
    responses={200: OpenApiResponse(description='Access token renovado')},
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


class MeView(APIView):
    @extend_schema(
        summary='Perfil del usuario actual',
        description='Devuelve los datos básicos del usuario autenticado y sus membresías.',
    )
    def get(self, request):
        if request.user.is_superuser:
            communities = Community.objects.all().order_by('id')
            memberships_payload = [
                {
                    'community_id': c.id,
                    'community_name': c.name,
                    'status': Membership.Status.APPROVED,
                    'role_in_community': 'superadmin',
                }
                for c in communities
            ]
        else:
            memberships = (
                Membership.objects.filter(user=request.user)
                .select_related('community')
                .order_by('community_id')
            )
            memberships_payload = [
                {
                    'community_id': m.community_id,
                    'community_name': m.community.name,
                    'status': m.status,
                    'role_in_community': m.role_in_community,
                }
                for m in memberships
            ]

        try:
            display_name = request.user.profile.display_name
        except ObjectDoesNotExist:
            display_name = ''

        data = {
            'id': request.user.id,
            'email': request.user.email,
            'display_name': display_name,
            'is_superadmin': bool(request.user.is_superuser),
            'communities': memberships_payload,
        }
        return Response(data)
