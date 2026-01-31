from django.conf import settings
from django.db import models


class Community(models.Model):
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'pending'
        APPROVED = 'approved', 'approved'
        REJECTED = 'rejected', 'rejected'
        EXPELLED = 'expelled', 'expelled'

    class Role(models.TextChoices):
        MEMBER = 'member', 'member'
        MODERATOR = 'moderator', 'moderator'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)
    role_in_community = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'community')
        indexes = [
            models.Index(fields=['community', 'status']),
        ]

    def __str__(self):
        return f'{self.user_id} -> {self.community_id} ({self.status})'
