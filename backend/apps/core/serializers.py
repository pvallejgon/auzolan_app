from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from apps.communities.models import Community, Membership
from apps.profiles.models import Profile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    display_name = serializers.CharField(max_length=80)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este email ya está registrado.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data['email'].lower()
        password = validated_data['password']
        display_name = validated_data['display_name']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
        )
        Profile.objects.create(user=user, display_name=display_name)
        community, _ = Community.objects.get_or_create(
            name='Comunidad Demo',
            defaults={'description': 'Comunidad por defecto para el MVP.'},
        )
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
    communities = serializers.ListField()
