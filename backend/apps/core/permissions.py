from rest_framework.permissions import BasePermission
from apps.communities.models import Membership
from apps.chat.models import Conversation


class IsMemberOfCommunityApproved(BasePermission):
    message = 'No perteneces a la comunidad o no estás aprobado.'

    def has_permission(self, request, view):
        community_id = None
        if hasattr(view, 'get_community_id'):
            community_id = view.get_community_id()
        if community_id is None:
            community_id = request.data.get('community_id') or request.query_params.get('community_id')
        if not community_id:
            return True
        return Membership.objects.filter(
            user=request.user,
            community_id=community_id,
            status=Membership.Status.APPROVED,
        ).exists()


class IsRequestCreator(BasePermission):
    message = 'Solo el creador puede realizar esta acción.'

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'created_by_user_id', None) == request.user.id


class IsConversationParticipant(BasePermission):
    message = 'Solo participantes pueden acceder a esta conversación.'

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Conversation):
            request_obj = obj.request
        else:
            request_obj = getattr(obj, 'request', None)
        if request_obj is None:
            return False
        if request_obj.created_by_user_id == request.user.id:
            return True
        accepted_offer = request_obj.accepted_offer
        return accepted_offer is not None and accepted_offer.volunteer_user_id == request.user.id
