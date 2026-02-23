from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.reports.models import Report


class ReportSerializer(serializers.ModelSerializer):
    reporter_user_id = serializers.IntegerField(read_only=True)
    reporter_display_name = serializers.SerializerMethodField()
    request_id = serializers.IntegerField(read_only=True)
    request_title = serializers.CharField(source='request.title', read_only=True)
    request_status = serializers.CharField(source='request.status', read_only=True)
    request_community_id = serializers.IntegerField(source='request.community_id', read_only=True)
    request_community_name = serializers.CharField(source='request.community.name', read_only=True)

    def get_reporter_display_name(self, obj):
        reporter = getattr(obj, 'reporter_user', None)
        if not reporter:
            return ''

        try:
            profile = reporter.profile
        except ObjectDoesNotExist:
            profile = None

        if profile and profile.display_name:
            return profile.display_name
        if reporter.email:
            return reporter.email
        return f'Usuario #{reporter.id}'

    class Meta:
        model = Report
        fields = (
            'id',
            'reporter_user_id',
            'reporter_display_name',
            'request_id',
            'request_title',
            'request_status',
            'request_community_id',
            'request_community_name',
            'reason',
            'description',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('status', 'created_at', 'updated_at')

