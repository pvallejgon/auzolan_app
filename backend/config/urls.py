from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.views import RegisterView, MeView, CustomTokenObtainPairView, CustomTokenRefreshView
from apps.communities.views import (
    CommunityListView,
    JoinCommunityView,
    CommunityMembersListView,
    CommunityMemberUpdateView,
)
from apps.profiles.views import MeProfileView
from apps.requests.views import (
    RequestListCreateView,
    RequestDetailView,
    RequestCloseView,
    OfferListCreateView,
    AcceptOfferView,
    ModerationRequestCloseView,
    ModerationRequestDeleteView,
)
from apps.chat.views import RequestConversationView, MessageListCreateView
from apps.reports.views import ReportCreateView, ReportListView, ReportStatusUpdateView
from apps.loans.views import (
    LoanListCreateView,
    LoanDetailView,
    LoanRequestListCreateView,
    LoanRequestAcceptView,
    LoanRequestRejectView,
    LoanMarkReturnedView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/register', RegisterView.as_view()),
    path('api/auth/token', CustomTokenObtainPairView.as_view()),
    path('api/auth/token/refresh', CustomTokenRefreshView.as_view()),
    path('api/me', MeView.as_view()),
    path('api/profile', MeProfileView.as_view()),
    path('api/communities', CommunityListView.as_view()),
    path('api/communities/<int:community_id>/join', JoinCommunityView.as_view()),
    path('api/communities/<int:community_id>/members', CommunityMembersListView.as_view()),
    path('api/communities/<int:community_id>/members/<int:user_id>', CommunityMemberUpdateView.as_view()),
    path('api/requests', RequestListCreateView.as_view()),
    path('api/requests/<int:request_id>', RequestDetailView.as_view()),
    path('api/requests/<int:request_id>/close', RequestCloseView.as_view()),
    path('api/requests/<int:request_id>/offers', OfferListCreateView.as_view()),
    path('api/requests/<int:request_id>/accept-offer/<int:offer_id>', AcceptOfferView.as_view()),
    path('api/moderation/requests/<int:request_id>/close', ModerationRequestCloseView.as_view()),
    path('api/moderation/requests/<int:request_id>', ModerationRequestDeleteView.as_view()),
    path('api/requests/<int:request_id>/conversation', RequestConversationView.as_view()),
    path('api/conversations/<int:conversation_id>/messages', MessageListCreateView.as_view()),
    path('api/requests/<int:request_id>/reports', ReportCreateView.as_view()),
    path('api/reports', ReportListView.as_view()),
    path('api/reports/<int:report_id>/status', ReportStatusUpdateView.as_view()),
    path('api/loans', LoanListCreateView.as_view()),
    path('api/loans/<int:loan_id>', LoanDetailView.as_view()),
    path('api/loans/<int:loan_id>/requests', LoanRequestListCreateView.as_view()),
    path('api/loans/<int:loan_id>/requests/<int:loan_request_id>/accept', LoanRequestAcceptView.as_view()),
    path('api/loans/<int:loan_id>/requests/<int:loan_request_id>/reject', LoanRequestRejectView.as_view()),
    path('api/loans/<int:loan_id>/mark-returned', LoanMarkReturnedView.as_view()),
]
