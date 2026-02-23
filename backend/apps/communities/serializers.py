from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.communities.models import Community, Membership


class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = ('id', 'name', 'description')


class MembershipSerializer(serializers.ModelSerializer):
    community_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Membership
        fields = ('community_id', 'status', 'role_in_community')


class CommunityMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    display_name = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = (
            'user_id',
            'email',
            'display_name',
            'bio',
            'status',
            'role_in_community',
            'joined_at',
            'updated_at',
        )

    def get_display_name(self, obj):
        user = getattr(obj, 'user', None)
        if not user:
            return ''

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        if profile and profile.display_name:
            return profile.display_name
        return user.email or f'Usuario {user.id}'

    def get_bio(self, obj):
        user = getattr(obj, 'user', None)
        if not user:
            return ''

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        return profile.bio if profile else ''


class CommunityMemberUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=80, required=False)
    bio = serializers.CharField(max_length=280, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Membership.Status.choices, required=False)
    role_in_community = serializers.ChoiceField(choices=Membership.Role.choices, required=False)
