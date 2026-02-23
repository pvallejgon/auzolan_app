import logging

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import Conversation
from apps.core.pagination import StandardResultsPagination
from apps.core.permissions import (
    has_approved_membership,
    is_moderator_in_community,
    is_superadmin,
    normalize_community_id,
)
from apps.requests.models import Request, VolunteerOffer
from apps.requests.serializers import (
    RequestSerializer,
    RequestUpdateSerializer,
    VolunteerOfferSerializer,
)

logger = logging.getLogger(__name__)


class RequestListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar peticiones',
        description='Lista peticiones por comunidad con filtros opcionales y paginación.',
        parameters=[
            OpenApiParameter(name='community_id', description='ID de comunidad (obligatorio en MVP)', required=True, type=int),
            OpenApiParameter(name='status', description='Filtrar por estado', required=False, type=str),
            OpenApiParameter(name='category', description='Filtrar por categoría', required=False, type=str),
            OpenApiParameter(name='mine', description='Si es 1/true, solo peticiones del usuario', required=False, type=str),
            OpenApiParameter(name='order', description='latest (por defecto) u oldest', required=False, type=str),
            OpenApiParameter(name='page', description='Página', required=False, type=int),
            OpenApiParameter(name='page_size', description='Tamaño de página', required=False, type=int),
        ],
        responses={200: RequestSerializer(many=True)},
    )
    def get(self, request):
        community_id = request.query_params.get('community_id')
        if not community_id:
            return Response({'detail': 'community_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)
        community_id_int = normalize_community_id(community_id)
        if community_id_int is None:
            return Response({'detail': 'community_id inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        if not has_approved_membership(request.user, community_id_int):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = (
            Request.objects.filter(community_id=community_id_int)
            .select_related('created_by_user', 'created_by_user__profile')
            .annotate(offers_count=Count('offers'))
            .order_by('-created_at')
        )
        status_filter = request.query_params.get('status')
        category_filter = request.query_params.get('category')
        mine_filter = request.query_params.get('mine')
        order_filter = request.query_params.get('order')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category_filter:
            queryset = queryset.filter(category=category_filter)
        if mine_filter in ['1', 'true', 'True', 'yes', 'si', 'sí']:
            queryset = queryset.filter(created_by_user=request.user)
        if order_filter == 'oldest':
            queryset = queryset.order_by('created_at')

        paginator = StandardResultsPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = RequestSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary='Crear petición',
        description='Crea una petición en una comunidad donde el usuario está aprobado.',
        request=RequestSerializer,
        responses={201: RequestSerializer},
    )
    def post(self, request):
        serializer = RequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        community = serializer.validated_data['community']
        if not has_approved_membership(request.user, community.id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        instance = serializer.save(created_by_user=request.user)
        return Response(RequestSerializer(instance).data, status=status.HTTP_201_CREATED)


class RequestDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Detalle de petición',
        description='Devuelve el detalle, flags de permisos y conteos para la petición.',
    )
    def get(self, request, request_id):
        obj = get_object_or_404(
            Request.objects.select_related('created_by_user', 'created_by_user__profile'),
            id=request_id,
        )
        if not has_approved_membership(request.user, obj.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        offers_count = obj.offers.count()
        can_offer = False
        if obj.status == Request.Status.OPEN and obj.created_by_user_id != request.user.id:
            can_offer = not VolunteerOffer.objects.filter(request=obj, volunteer_user=request.user).exists()

        can_accept = obj.status == Request.Status.OPEN and (
            obj.created_by_user_id == request.user.id or is_superadmin(request.user)
        )
        can_close = (
            obj.status in [Request.Status.OPEN, Request.Status.IN_PROGRESS]
            and (obj.created_by_user_id == request.user.id or is_superadmin(request.user))
        )
        can_moderate = is_moderator_in_community(request.user, obj.community_id)

        return Response(
            {
                'request': RequestSerializer(obj).data,
                'offers_count': offers_count,
                'accepted_offer_id': obj.accepted_offer_id,
                'can_offer': can_offer,
                'can_accept': can_accept,
                'can_close': can_close,
                'can_moderate': can_moderate,
            }
        )

    @extend_schema(
        summary='Editar petición',
        description='Edita una petición solo si el usuario es creador y está en estado open.',
        request=RequestUpdateSerializer,
        responses={200: RequestSerializer},
    )
    def patch(self, request, request_id):
        obj = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, obj.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if obj.created_by_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo el creador puede editar.'}, status=status.HTTP_403_FORBIDDEN)
        if obj.status != Request.Status.OPEN:
            return Response({'detail': 'Solo se puede editar si está open.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RequestUpdateSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RequestSerializer(obj).data)


class RequestCloseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Cerrar petición',
        description='Cierra una petición como resolved o cancelled (solo creador o superadmin).',
    )
    def post(self, request, request_id):
        obj = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, obj.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if obj.created_by_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo el creador puede cerrar.'}, status=status.HTTP_403_FORBIDDEN)

        status_value = request.data.get('status')
        if status_value not in [Request.Status.RESOLVED, Request.Status.CANCELLED]:
            return Response({'detail': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        if obj.status not in [Request.Status.OPEN, Request.Status.IN_PROGRESS]:
            return Response({'detail': 'No se puede cerrar en este estado.'}, status=status.HTTP_400_BAD_REQUEST)

        obj.status = status_value
        obj.closed_at = timezone.now()
        obj.save(update_fields=['status', 'closed_at', 'updated_at'])
        return Response(RequestSerializer(obj).data)


class OfferListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar ofertas',
        description='Devuelve ofertas de una petición. Creador, moderador de comunidad o superadmin.',
        responses={200: VolunteerOfferSerializer(many=True)},
    )
    def get(self, request, request_id):
        req = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, req.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        if req.created_by_user_id != request.user.id and not is_moderator_in_community(request.user, req.community_id):
            return Response({'detail': 'Sin permisos para ver las ofertas.'}, status=status.HTTP_403_FORBIDDEN)

        offers = (
            VolunteerOffer.objects.filter(request=req)
            .select_related('volunteer_user', 'volunteer_user__profile')
            .order_by('-created_at')
        )
        serializer = VolunteerOfferSerializer(offers, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Crear oferta de voluntariado',
        description='Crea una oferta en una petición open (no creador, no duplicada).',
        request=VolunteerOfferSerializer,
        responses={201: VolunteerOfferSerializer},
    )
    def post(self, request, request_id):
        req = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, req.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if req.status != Request.Status.OPEN:
            return Response({'detail': 'La petición no está abierta.'}, status=status.HTTP_400_BAD_REQUEST)
        if req.created_by_user_id == request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'No puedes ofrecerte a tu propia petición.'}, status=status.HTTP_400_BAD_REQUEST)
        if VolunteerOffer.objects.filter(request=req, volunteer_user=request.user).exists():
            return Response({'detail': 'Ya tienes una oferta en esta petición.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VolunteerOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = VolunteerOffer.objects.create(
            request=req,
            volunteer_user=request.user,
            message=serializer.validated_data.get('message', ''),
        )
        return Response(VolunteerOfferSerializer(offer).data, status=status.HTTP_201_CREATED)


class AcceptOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    @extend_schema(
        summary='Aceptar oferta',
        description='Acepta una oferta y rechaza el resto, pone la petición en in_progress y crea conversación.',
        responses={200: RequestSerializer},
    )
    def post(self, request, request_id, offer_id):
        req = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, req.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if req.created_by_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo el creador puede aceptar.'}, status=status.HTTP_403_FORBIDDEN)
        if req.status != Request.Status.OPEN:
            return Response({'detail': 'La petición no está abierta.'}, status=status.HTTP_400_BAD_REQUEST)

        offer = get_object_or_404(VolunteerOffer, id=offer_id, request=req)
        if offer.status != VolunteerOffer.Status.OFFERED:
            return Response({'detail': 'La oferta no está disponible.'}, status=status.HTTP_400_BAD_REQUEST)

        offer.status = VolunteerOffer.Status.ACCEPTED
        offer.save(update_fields=['status', 'updated_at'])

        VolunteerOffer.objects.filter(request=req).exclude(id=offer.id).update(
            status=VolunteerOffer.Status.REJECTED,
            updated_at=timezone.now(),
        )

        req.status = Request.Status.IN_PROGRESS
        req.accepted_offer = offer
        req.save(update_fields=['status', 'accepted_offer', 'updated_at'])

        Conversation.objects.get_or_create(request=req)
        return Response(RequestSerializer(req).data)


class ModerationRequestCloseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Moderación: cerrar petición',
        description='Moderador de comunidad o superadmin puede cerrar como resolved/cancelled.',
        responses={200: RequestSerializer},
    )
    def post(self, request, request_id):
        req = get_object_or_404(Request, id=request_id)
        if not is_moderator_in_community(request.user, req.community_id):
            return Response({'detail': 'No tienes permisos de moderación en esta comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        status_value = request.data.get('status', Request.Status.CANCELLED)
        if status_value not in [Request.Status.RESOLVED, Request.Status.CANCELLED]:
            return Response({'detail': 'Estado inválido para moderación.'}, status=status.HTTP_400_BAD_REQUEST)
        if req.status not in [Request.Status.OPEN, Request.Status.IN_PROGRESS]:
            return Response({'detail': 'No se puede cerrar en este estado.'}, status=status.HTTP_400_BAD_REQUEST)

        req.status = status_value
        req.closed_at = timezone.now()
        req.save(update_fields=['status', 'closed_at', 'updated_at'])

        logger.info('Moderación cierre de petición', extra={'request_id': req.id, 'actor_user_id': request.user.id})
        return Response(RequestSerializer(req).data)


class ModerationRequestDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Moderación: eliminar petición',
        description='Moderador de comunidad o superadmin elimina una petición.',
        responses={204: None},
    )
    def delete(self, request, request_id):
        req = get_object_or_404(Request, id=request_id)
        if not is_moderator_in_community(request.user, req.community_id):
            return Response({'detail': 'No tienes permisos de moderación en esta comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        logger.info('Moderación borrado de petición', extra={'request_id': req.id, 'actor_user_id': request.user.id})
        req.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
