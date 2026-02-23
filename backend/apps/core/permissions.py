from rest_framework.permissions import BasePermission

from apps.chat.models import Conversation
from apps.communities.models import Membership


def is_superadmin(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def normalize_community_id(community_id):
    try:
        return int(community_id)
    except (TypeError, ValueError):
        return None


def has_approved_membership(user, community_id):
    if is_superadmin(user):
        return True
    if not user or not user.is_authenticated:
        return False

    community_id = normalize_community_id(community_id)
    if community_id is None:
        return False

    return Membership.objects.filter(
        user=user,
        community_id=community_id,
        status=Membership.Status.APPROVED,
    ).exists()


def is_moderator_in_community(user, community_id):
    if is_superadmin(user):
        return True
    if not user or not user.is_authenticated:
        return False

    community_id = normalize_community_id(community_id)
    if community_id is None:
        return False

    return Membership.objects.filter(
        user=user,
        community_id=community_id,
        status=Membership.Status.APPROVED,
        role_in_community=Membership.Role.MODERATOR,
    ).exists()


def get_moderated_community_ids(user):
    if is_superadmin(user):
        from apps.communities.models import Community

        return list(Community.objects.values_list('id', flat=True))
    return list(
        Membership.objects.filter(
            user=user,
            status=Membership.Status.APPROVED,
            role_in_community=Membership.Role.MODERATOR,
        ).values_list('community_id', flat=True)
    )


class IsMemberOfCommunityApproved(BasePermission):
    message = 'No perteneces a la comunidad o no estás aprobado.'

    def has_permission(self, request, view):
        if is_superadmin(request.user):
            return True

        community_id = None
        if hasattr(view, 'get_community_id'):
            community_id = view.get_community_id()
        if community_id is None:
            community_id = request.data.get('community_id') or request.query_params.get('community_id')
        if not community_id:
            return True
        return has_approved_membership(request.user, community_id)


class IsRequestCreator(BasePermission):
    message = 'Solo el creador puede realizar esta acción.'

    def has_object_permission(self, request, view, obj):
        if is_superadmin(request.user):
            return True
        return getattr(obj, 'created_by_user_id', None) == request.user.id


class IsConversationParticipant(BasePermission):
    message = 'Solo participantes pueden acceder a esta conversación.'

    def has_object_permission(self, request, view, obj):
        if is_superadmin(request.user):
            return True

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
