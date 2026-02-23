import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardResultsPagination
from apps.core.permissions import (
    get_moderated_community_ids,
    has_approved_membership,
    is_moderator_in_community,
    is_superadmin,
    normalize_community_id,
)
from apps.reports.models import Report
from apps.reports.serializers import ReportSerializer
from apps.requests.models import Request

logger = logging.getLogger(__name__)


class ReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Crear reporte',
        description='Crea un reporte sobre una petición dentro de la comunidad.',
        request=ReportSerializer,
        responses={201: ReportSerializer},
    )
    def post(self, request, request_id):
        req = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, req.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = Report.objects.create(
            reporter_user=request.user,
            request=req,
            reason=serializer.validated_data['reason'],
            description=serializer.validated_data.get('description', ''),
        )
        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)


class ReportListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar reportes',
        description='Moderadores ven reportes de sus comunidades; superadmin ve todos.',
        parameters=[
            OpenApiParameter(name='community_id', description='Filtrar por comunidad', required=False, type=int),
            OpenApiParameter(name='status', description='Filtrar por estado del reporte', required=False, type=str),
            OpenApiParameter(name='page', description='Página', required=False, type=int),
            OpenApiParameter(name='page_size', description='Tamaño de página', required=False, type=int),
        ],
        responses={200: ReportSerializer(many=True)},
    )
    def get(self, request):
        community_id = request.query_params.get('community_id')
        report_status = request.query_params.get('status')

        queryset = Report.objects.select_related(
            'request',
            'request__community',
            'reporter_user',
            'reporter_user__profile',
        ).order_by('-created_at')

        if is_superadmin(request.user):
            if community_id:
                community_id_int = normalize_community_id(community_id)
                if community_id_int is None:
                    return Response({'detail': 'community_id inválido.'}, status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(request__community_id=community_id_int)
        else:
            moderated_community_ids = get_moderated_community_ids(request.user)
            if not moderated_community_ids:
                return Response({'detail': 'No tienes permisos de moderación.'}, status=status.HTTP_403_FORBIDDEN)

            if community_id:
                community_id_int = normalize_community_id(community_id)
                if community_id_int is None:
                    return Response({'detail': 'community_id inválido.'}, status=status.HTTP_400_BAD_REQUEST)

                if community_id_int not in moderated_community_ids:
                    return Response({'detail': 'No puedes ver reportes de esa comunidad.'}, status=status.HTTP_403_FORBIDDEN)
                queryset = queryset.filter(request__community_id=community_id_int)
            else:
                queryset = queryset.filter(request__community_id__in=moderated_community_ids)

        if report_status:
            queryset = queryset.filter(status=report_status)

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ReportSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ReportStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Actualizar estado de reporte',
        description='Moderador de comunidad o superadmin puede cambiar estado del reporte.',
        request={'type': 'object', 'properties': {'status': {'type': 'string'}}},
        responses={200: ReportSerializer},
    )
    def post(self, request, report_id):
        report = get_object_or_404(
            Report.objects.select_related('request', 'request__community'),
            id=report_id,
        )
        if not is_moderator_in_community(request.user, report.request.community_id):
            return Response({'detail': 'No tienes permisos de moderación en esta comunidad.'}, status=status.HTTP_403_FORBIDDEN)

        status_value = request.data.get('status')
        if status_value not in [Report.Status.OPEN, Report.Status.IN_REVIEW, Report.Status.CLOSED]:
            return Response({'detail': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        report.status = status_value
        report.save(update_fields=['status', 'updated_at'])

        logger.info(
            'Moderación actualización de reporte',
            extra={
                'report_id': report.id,
                'request_id': report.request_id,
                'community_id': report.request.community_id,
                'actor_user_id': request.user.id,
                'new_status': status_value,
            },
        )
        return Response(ReportSerializer(report).data)
