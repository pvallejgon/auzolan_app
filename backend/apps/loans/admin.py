from django.contrib import admin

from apps.loans.models import LoanItem, LoanRequest


@admin.register(LoanItem)
class LoanItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'community', 'owner_user', 'status', 'borrower_user', 'created_at')
    list_filter = ('status', 'community')
    search_fields = ('title', 'description')


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'requester_user', 'status', 'created_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('message',)
