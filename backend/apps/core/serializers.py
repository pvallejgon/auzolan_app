from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.communities.models import Community, Membership
from apps.profiles.models import Profile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    display_name = serializers.CharField(max_length=80)
    community_id = serializers.IntegerField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este email ya está registrado.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_community_id(self, value):
        if not Community.objects.filter(id=value).exists():
            raise serializers.ValidationError('Comunidad no válida.')
        return value

    def create(self, validated_data):
        email = validated_data['email'].lower()
        password = validated_data['password']
        display_name = validated_data['display_name']
        community = Community.objects.get(id=validated_data['community_id'])

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
        )
        Profile.objects.create(user=user, display_name=display_name)
        Membership.objects.get_or_create(
            user=user,
            community=community,
            defaults={
                'status': Membership.Status.APPROVED,
                'role_in_community': Membership.Role.MEMBER,
                'joined_at': timezone.now(),
            },
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop(self.username_field, None)

    def validate(self, attrs):
        attrs[self.username_field] = (attrs.get('email') or '').lower()
        return super().validate(attrs)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField()
    is_superadmin = serializers.BooleanField()
    communities = serializers.ListField()
