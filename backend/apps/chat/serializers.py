from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from apps.chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    conversation_id = serializers.IntegerField(read_only=True)
    sender_user_id = serializers.IntegerField(read_only=True)
    sender_display_name = serializers.SerializerMethodField()

    def get_sender_display_name(self, obj):
        sender = getattr(obj, 'sender_user', None)
        if not sender:
            return ''

        try:
            profile = sender.profile
        except ObjectDoesNotExist:
            profile = None
        if profile and profile.display_name:
            return profile.display_name
        if sender.email:
            return sender.email
        return f'Usuario #{sender.id}'

    class Meta:
        model = Message
        fields = ('id', 'conversation_id', 'sender_user_id', 'sender_display_name', 'body', 'created_at')
        read_only_fields = ('created_at',)
