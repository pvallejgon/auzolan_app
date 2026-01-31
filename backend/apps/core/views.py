from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.core.serializers import RegisterSerializer, CustomTokenObtainPairSerializer
from apps.communities.models import Membership

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary='Registro de usuario',
        description='Crea un usuario, su perfil y la membresía aprobada en la Comunidad Demo.',
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
        memberships = Membership.objects.filter(user=request.user).select_related('community')
        data = {
            'id': request.user.id,
            'email': request.user.email,
            'display_name': request.user.profile.display_name if hasattr(request.user, 'profile') else '',
            'communities': [
                {
                    'community_id': m.community_id,
                    'status': m.status,
                    'role_in_community': m.role_in_community,
                }
                for m in memberships
            ],
        }
        return Response(data)
