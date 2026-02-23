from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardResultsPagination
from apps.core.permissions import has_approved_membership, is_superadmin, normalize_community_id
from apps.loans.models import LoanItem, LoanRequest
from apps.loans.serializers import LoanItemSerializer, LoanItemUpdateSerializer, LoanRequestSerializer


class LoanListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar items de préstamo',
        description='Lista items por comunidad con filtros opcionales y paginación.',
        parameters=[
            OpenApiParameter(name='community_id', description='ID de comunidad', required=True, type=int),
            OpenApiParameter(name='status', description='available o loaned', required=False, type=str),
            OpenApiParameter(name='mine', description='Si es 1/true, solo items del usuario', required=False, type=str),
            OpenApiParameter(name='order', description='latest (por defecto) u oldest', required=False, type=str),
            OpenApiParameter(name='page', description='Página', required=False, type=int),
            OpenApiParameter(name='page_size', description='Tamaño de página', required=False, type=int),
        ],
        responses={200: LoanItemSerializer(many=True)},
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
            LoanItem.objects.filter(community_id=community_id_int)
            .select_related('owner_user', 'owner_user__profile', 'borrower_user', 'borrower_user__profile')
            .annotate(
                pending_requests_count=Count(
                    'requests',
                    filter=Q(requests__status=LoanRequest.Status.PENDING),
                )
            )
            .order_by('-created_at')
        )

        status_filter = request.query_params.get('status')
        mine_filter = request.query_params.get('mine')
        order_filter = request.query_params.get('order')

        if status_filter in [LoanItem.Status.AVAILABLE, LoanItem.Status.LOANED]:
            queryset = queryset.filter(status=status_filter)
        if mine_filter in ['1', 'true', 'True', 'yes', 'si', 'sí']:
            queryset = queryset.filter(owner_user=request.user)
        if order_filter == 'oldest':
            queryset = queryset.order_by('created_at')

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = LoanItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary='Crear item de préstamo',
        description='Crea un item para prestar en una comunidad donde el usuario está aprobado.',
        request=LoanItemSerializer,
        responses={201: LoanItemSerializer},
    )
    def post(self, request):
        serializer = LoanItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        community = serializer.validated_data['community']
        if not has_approved_membership(request.user, community.id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        item = serializer.save(owner_user=request.user)
        return Response(LoanItemSerializer(item).data, status=status.HTTP_201_CREATED)


class LoanDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Detalle de item de préstamo',
        description='Devuelve detalle y flags de permisos/acciones para el item.',
        responses={200: LoanItemSerializer},
    )
    def get(self, request, loan_id):
        item = get_object_or_404(
            LoanItem.objects.select_related(
                'owner_user',
                'owner_user__profile',
                'borrower_user',
                'borrower_user__profile',
            ).annotate(
                pending_requests_count=Count(
                    'requests',
                    filter=Q(requests__status=LoanRequest.Status.PENDING),
                )
            ),
            id=loan_id,
        )
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        has_pending_request = LoanRequest.objects.filter(
            item=item,
            requester_user=request.user,
            status=LoanRequest.Status.PENDING,
        ).exists()
        can_request = (
            item.status == LoanItem.Status.AVAILABLE
            and item.owner_user_id != request.user.id
            and not has_pending_request
        )
        can_manage_item = item.owner_user_id == request.user.id or is_superadmin(request.user)
        can_manage_requests = can_manage_item
        can_mark_returned = can_manage_item and item.status == LoanItem.Status.LOANED

        return Response(
            {
                'item': LoanItemSerializer(item).data,
                'can_request': can_request,
                'can_manage_item': can_manage_item,
                'can_manage_requests': can_manage_requests,
                'can_mark_returned': can_mark_returned,
            }
        )

    @extend_schema(
        summary='Editar item de préstamo',
        description='Solo propietario o superadmin puede editar título y descripción.',
        request=LoanItemUpdateSerializer,
        responses={200: LoanItemSerializer},
    )
    def patch(self, request, loan_id):
        item = get_object_or_404(LoanItem, id=loan_id)
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if item.owner_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo quien presta puede editar este item.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = LoanItemUpdateSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(LoanItemSerializer(item).data)


class LoanRequestListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar solicitudes de préstamo',
        description='Solo quien presta el item (o superadmin) puede ver las solicitudes.',
        responses={200: LoanRequestSerializer(many=True)},
    )
    def get(self, request, loan_id):
        item = get_object_or_404(LoanItem, id=loan_id)
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if item.owner_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Sin permisos para ver solicitudes.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = (
            LoanRequest.objects.filter(item=item)
            .select_related('requester_user', 'requester_user__profile')
            .order_by('-created_at')
        )
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = LoanRequestSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary='Solicitar préstamo',
        description='Crea una solicitud de préstamo si el item está disponible.',
        request=LoanRequestSerializer,
        responses={201: LoanRequestSerializer},
    )
    def post(self, request, loan_id):
        item = get_object_or_404(LoanItem, id=loan_id)
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if item.status != LoanItem.Status.AVAILABLE:
            return Response({'detail': 'El item no está disponible.'}, status=status.HTTP_400_BAD_REQUEST)
        if item.owner_user_id == request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'No puedes solicitar tu propio item.'}, status=status.HTTP_400_BAD_REQUEST)
        if LoanRequest.objects.filter(item=item, requester_user=request.user, status=LoanRequest.Status.PENDING).exists():
            return Response({'detail': 'Ya tienes una solicitud pendiente para este item.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan_request = LoanRequest.objects.create(
            item=item,
            requester_user=request.user,
            message=serializer.validated_data.get('message', ''),
        )
        return Response(LoanRequestSerializer(loan_request).data, status=status.HTTP_201_CREATED)


class LoanRequestAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    @extend_schema(
        summary='Aceptar solicitud de préstamo',
        description='Solo quien presta el item o superadmin puede aceptar; el item pasa a loaned.',
        responses={200: LoanItemSerializer},
    )
    def post(self, request, loan_id, loan_request_id):
        item = get_object_or_404(LoanItem, id=loan_id)
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if item.owner_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo quien presta puede aceptar solicitudes.'}, status=status.HTTP_403_FORBIDDEN)
        if item.status != LoanItem.Status.AVAILABLE:
            return Response({'detail': 'El item no está disponible para aceptar solicitudes.'}, status=status.HTTP_400_BAD_REQUEST)

        loan_request = get_object_or_404(LoanRequest, id=loan_request_id, item=item)
        if loan_request.status != LoanRequest.Status.PENDING:
            return Response({'detail': 'La solicitud no está pendiente.'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        loan_request.status = LoanRequest.Status.ACCEPTED
        loan_request.responded_at = now
        loan_request.save(update_fields=['status', 'responded_at', 'updated_at'])

        LoanRequest.objects.filter(item=item, status=LoanRequest.Status.PENDING).exclude(id=loan_request.id).update(
            status=LoanRequest.Status.REJECTED,
            responded_at=now,
            updated_at=now,
        )

        item.status = LoanItem.Status.LOANED
        item.borrower_user = loan_request.requester_user
        item.loaned_at = now
        item.returned_at = None
        item.save(update_fields=['status', 'borrower_user', 'loaned_at', 'returned_at', 'updated_at'])

        return Response(LoanItemSerializer(item).data)


class LoanRequestRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Rechazar solicitud de préstamo',
        description='Solo quien presta el item o superadmin puede rechazar solicitudes pendientes.',
        responses={200: LoanRequestSerializer},
    )
    def post(self, request, loan_id, loan_request_id):
        item = get_object_or_404(LoanItem, id=loan_id)
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if item.owner_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo quien presta puede rechazar solicitudes.'}, status=status.HTTP_403_FORBIDDEN)

        loan_request = get_object_or_404(LoanRequest, id=loan_request_id, item=item)
        if loan_request.status != LoanRequest.Status.PENDING:
            return Response({'detail': 'La solicitud no está pendiente.'}, status=status.HTTP_400_BAD_REQUEST)

        loan_request.status = LoanRequest.Status.REJECTED
        loan_request.responded_at = timezone.now()
        loan_request.save(update_fields=['status', 'responded_at', 'updated_at'])
        return Response(LoanRequestSerializer(loan_request).data)


class LoanMarkReturnedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Marcar devolución de préstamo',
        description='Solo quien presta el item o superadmin puede marcarlo como devuelto.',
        responses={200: LoanItemSerializer},
    )
    def post(self, request, loan_id):
        item = get_object_or_404(LoanItem, id=loan_id)
        if not has_approved_membership(request.user, item.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if item.owner_user_id != request.user.id and not is_superadmin(request.user):
            return Response({'detail': 'Solo quien presta puede marcar la devolución.'}, status=status.HTTP_403_FORBIDDEN)
        if item.status != LoanItem.Status.LOANED:
            return Response({'detail': 'El item no está marcado como prestado.'}, status=status.HTTP_400_BAD_REQUEST)

        item.status = LoanItem.Status.AVAILABLE
        item.borrower_user = None
        item.returned_at = timezone.now()
        item.save(update_fields=['status', 'borrower_user', 'returned_at', 'updated_at'])
        return Response(LoanItemSerializer(item).data)
