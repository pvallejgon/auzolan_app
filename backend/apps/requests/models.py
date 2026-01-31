from django.conf import settings
from django.db import models
from apps.communities.models import Community


class Request(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'open'
        IN_PROGRESS = 'in_progress', 'in_progress'
        RESOLVED = 'resolved', 'resolved'
        CANCELLED = 'cancelled', 'cancelled'

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=60)
    time_window_text = models.CharField(max_length=120, blank=True)
    location_area_text = models.CharField(max_length=120, blank=True)
    location_radius_km = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    accepted_offer = models.ForeignKey('VolunteerOffer', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_for')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['community', 'status']),
            models.Index(fields=['community', 'category']),
            models.Index(fields=['created_by_user']),
        ]

    def __str__(self):
        return self.title


class VolunteerOffer(models.Model):
    class Status(models.TextChoices):
        OFFERED = 'offered', 'offered'
        ACCEPTED = 'accepted', 'accepted'
        REJECTED = 'rejected', 'rejected'
        WITHDRAWN = 'withdrawn', 'withdrawn'

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='offers')
    volunteer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=280, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFERED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('request', 'volunteer_user')
        indexes = [
            models.Index(fields=['request', 'status']),
        ]

    def __str__(self):
        return f'Offer {self.id} -> Request {self.request_id}'
