from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.views import RegisterView, MeView, CustomTokenObtainPairView, CustomTokenRefreshView
from apps.communities.views import CommunityListView, JoinCommunityView
from apps.requests.views import (
    RequestListCreateView,
    RequestDetailView,
    RequestCloseView,
    OfferListCreateView,
    AcceptOfferView,
)
from apps.chat.views import RequestConversationView, MessageListCreateView
from apps.reports.views import ReportCreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/register', RegisterView.as_view()),
    path('api/auth/token', CustomTokenObtainPairView.as_view()),
    path('api/auth/token/refresh', CustomTokenRefreshView.as_view()),
    path('api/me', MeView.as_view()),
    path('api/communities', CommunityListView.as_view()),
    path('api/communities/<int:community_id>/join', JoinCommunityView.as_view()),
    path('api/requests', RequestListCreateView.as_view()),
    path('api/requests/<int:request_id>', RequestDetailView.as_view()),
    path('api/requests/<int:request_id>/close', RequestCloseView.as_view()),
    path('api/requests/<int:request_id>/offers', OfferListCreateView.as_view()),
    path('api/requests/<int:request_id>/accept-offer/<int:offer_id>', AcceptOfferView.as_view()),
    path('api/requests/<int:request_id>/conversation', RequestConversationView.as_view()),
    path('api/conversations/<int:conversation_id>/messages', MessageListCreateView.as_view()),
    path('api/requests/<int:request_id>/reports', ReportCreateView.as_view()),
]
