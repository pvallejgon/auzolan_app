from rest_framework import serializers
from apps.chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    conversation_id = serializers.IntegerField(read_only=True)
    sender_user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'conversation_id', 'sender_user_id', 'body', 'created_at')
        read_only_fields = ('created_at',)
