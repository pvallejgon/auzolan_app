from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.communities.models import Membership
from apps.reports.models import Report
from apps.reports.serializers import ReportSerializer
from apps.requests.models import Request


def is_member_approved(user, community_id):
    return Membership.objects.filter(
        user=user,
        community_id=community_id,
        status=Membership.Status.APPROVED,
    ).exists()


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
        if not is_member_approved(request.user, req.community_id):
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
