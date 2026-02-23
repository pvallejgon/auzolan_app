from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.communities.models import Community
from apps.requests.models import Request, VolunteerOffer


class RequestSerializer(serializers.ModelSerializer):
    community_id = serializers.PrimaryKeyRelatedField(source='community', queryset=Community.objects.all())
    created_by_user_id = serializers.IntegerField(read_only=True)
    accepted_offer_id = serializers.IntegerField(read_only=True)
    created_by_display_name = serializers.SerializerMethodField()
    offers_count = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = (
            'id',
            'community_id',
            'created_by_user_id',
            'created_by_display_name',
            'title',
            'description',
            'category',
            'time_window_text',
            'location_area_text',
            'location_radius_km',
            'status',
            'accepted_offer_id',
            'offers_count',
            'created_at',
            'updated_at',
            'closed_at',
        )
        read_only_fields = ('status', 'accepted_offer_id', 'created_at', 'updated_at', 'closed_at')

    def get_created_by_display_name(self, obj):
        user = getattr(obj, 'created_by_user', None)
        if not user:
            return ''

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        if profile and profile.display_name:
            return profile.display_name
        return user.email or f'Usuario {user.id}'

    def get_offers_count(self, obj):
        if hasattr(obj, 'offers_count'):
            return obj.offers_count
        return obj.offers.count()


class RequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ('title', 'description', 'category', 'time_window_text', 'location_area_text', 'location_radius_km')


class VolunteerOfferSerializer(serializers.ModelSerializer):
    request_id = serializers.IntegerField(read_only=True)
    volunteer_user_id = serializers.IntegerField(read_only=True)
    volunteer_display_name = serializers.SerializerMethodField()

    class Meta:
        model = VolunteerOffer
        fields = (
            'id',
            'request_id',
            'volunteer_user_id',
            'volunteer_display_name',
            'message',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('status', 'created_at', 'updated_at')

    def get_volunteer_display_name(self, obj):
        user = getattr(obj, 'volunteer_user', None)
        if not user:
            return ''

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        if profile and profile.display_name:
            return profile.display_name
        return user.email or f'Usuario {user.id}'
