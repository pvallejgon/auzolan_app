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
