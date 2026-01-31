from django.contrib import admin
from apps.profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'created_at')
    search_fields = ('display_name', 'user__email')
