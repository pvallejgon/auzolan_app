from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.chat.models import Conversation, Message
from apps.chat.serializers import MessageSerializer
from apps.core.permissions import has_approved_membership, is_superadmin
from apps.requests.models import Request
from apps.core.pagination import StandardResultsPagination


def is_participant(user, request_obj):
    if is_superadmin(user):
        return True
    if request_obj.created_by_user_id == user.id:
        return True
    accepted_offer = request_obj.accepted_offer
    return accepted_offer is not None and accepted_offer.volunteer_user_id == user.id


class RequestConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Obtener conversación de una petición',
        description='Devuelve conversation_id si el usuario es creador o voluntario aceptado.',
    )
    def get(self, request, request_id):
        req = get_object_or_404(Request, id=request_id)
        if not has_approved_membership(request.user, req.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if req.accepted_offer is None:
            return Response({'detail': 'No hay voluntario aceptado.'}, status=status.HTTP_400_BAD_REQUEST)
        if not is_participant(request.user, req):
            return Response({'detail': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
        conversation, _ = Conversation.objects.get_or_create(request=req)
        return Response({'conversation_id': conversation.id})


class MessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Listar mensajes',
        description='Devuelve mensajes paginados de una conversación. Solo participantes.',
        responses={200: MessageSerializer(many=True)},
    )
    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if not has_approved_membership(request.user, conversation.request.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if not is_participant(request.user, conversation.request):
            return Response({'detail': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
        messages = (
            Message.objects.filter(conversation=conversation)
            .select_related('sender_user', 'sender_user__profile')
            .order_by('-created_at')
        )
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary='Enviar mensaje',
        description='Envía un mensaje en la conversación (solo participantes).',
        request=MessageSerializer,
        responses={201: MessageSerializer},
    )
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        req = conversation.request
        if not has_approved_membership(request.user, req.community_id):
            return Response({'detail': 'No perteneces a la comunidad.'}, status=status.HTTP_403_FORBIDDEN)
        if not is_participant(request.user, req):
            return Response({'detail': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
        if req.status not in [Request.Status.IN_PROGRESS, Request.Status.RESOLVED]:
            return Response({'detail': 'El chat no está habilitado.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = Message.objects.create(
            conversation=conversation,
            sender_user=request.user,
            body=serializer.validated_data['body'],
        )
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
