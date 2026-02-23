from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.communities.models import Community
from apps.loans.models import LoanItem, LoanRequest


def resolve_display_name(user):
    if not user:
        return ''

    try:
        profile = user.profile
    except ObjectDoesNotExist:
        profile = None

    if profile and profile.display_name:
        return profile.display_name
    return user.email or f'Usuario #{user.id}'


class LoanItemSerializer(serializers.ModelSerializer):
    community_id = serializers.PrimaryKeyRelatedField(source='community', queryset=Community.objects.all())
    owner_user_id = serializers.IntegerField(read_only=True)
    owner_display_name = serializers.SerializerMethodField()
    borrower_user_id = serializers.IntegerField(read_only=True)
    borrower_display_name = serializers.SerializerMethodField()
    pending_requests_count = serializers.SerializerMethodField()

    class Meta:
        model = LoanItem
        fields = (
            'id',
            'community_id',
            'owner_user_id',
            'owner_display_name',
            'title',
            'description',
            'status',
            'borrower_user_id',
            'borrower_display_name',
            'loaned_at',
            'returned_at',
            'pending_requests_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'status',
            'borrower_user_id',
            'borrower_display_name',
            'loaned_at',
            'returned_at',
            'created_at',
            'updated_at',
        )

    def get_owner_display_name(self, obj):
        return resolve_display_name(getattr(obj, 'owner_user', None))

    def get_borrower_display_name(self, obj):
        return resolve_display_name(getattr(obj, 'borrower_user', None))

    def get_pending_requests_count(self, obj):
        if hasattr(obj, 'pending_requests_count'):
            return obj.pending_requests_count
        return obj.requests.filter(status=LoanRequest.Status.PENDING).count()


class LoanItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanItem
        fields = ('title', 'description')


class LoanRequestSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(read_only=True)
    requester_user_id = serializers.IntegerField(read_only=True)
    requester_display_name = serializers.SerializerMethodField()

    class Meta:
        model = LoanRequest
        fields = (
            'id',
            'item_id',
            'requester_user_id',
            'requester_display_name',
            'message',
            'status',
            'responded_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('status', 'responded_at', 'created_at', 'updated_at')

    def get_requester_display_name(self, obj):
        return resolve_display_name(getattr(obj, 'requester_user', None))
