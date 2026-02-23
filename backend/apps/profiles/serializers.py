from rest_framework import serializers

from apps.profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'display_name', 'bio')


class ProfileUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=80, required=False)
    bio = serializers.CharField(max_length=280, required=False, allow_blank=True)
