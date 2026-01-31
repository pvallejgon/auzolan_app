from django.contrib import admin
from apps.communities.models import Community, Membership


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'community', 'status', 'role_in_community', 'updated_at')
    list_filter = ('status', 'role_in_community')
