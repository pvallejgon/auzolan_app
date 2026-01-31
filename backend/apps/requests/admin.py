from django.contrib import admin
from apps.requests.models import Request, VolunteerOffer


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'community', 'status', 'created_at')
    list_filter = ('status', 'community')
    search_fields = ('title', 'description')


@admin.register(VolunteerOffer)
class VolunteerOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'volunteer_user', 'status', 'created_at')
    list_filter = ('status',)
