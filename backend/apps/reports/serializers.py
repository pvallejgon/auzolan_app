from rest_framework import serializers
from apps.reports.models import Report


class ReportSerializer(serializers.ModelSerializer):
    reporter_user_id = serializers.IntegerField(read_only=True)
    request_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Report
        fields = ('id', 'reporter_user_id', 'request_id', 'reason', 'description', 'status', 'created_at', 'updated_at')
        read_only_fields = ('status', 'created_at', 'updated_at')
