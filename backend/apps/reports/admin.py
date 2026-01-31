from django.contrib import admin
from apps.reports.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'reporter_user', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason')
    search_fields = ('description',)
