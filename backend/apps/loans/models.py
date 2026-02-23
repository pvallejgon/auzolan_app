from django.conf import settings
from django.db import models

from apps.communities.models import Community


class LoanItem(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'available'
        LOANED = 'loaned', 'loaned'

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='loan_items')
    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_loan_items')
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    borrower_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='borrowed_loan_items',
        null=True,
        blank=True,
    )
    loaned_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['community', 'status']),
            models.Index(fields=['owner_user', 'status']),
        ]

    def __str__(self):
        return self.title


class LoanRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'pending'
        ACCEPTED = 'accepted', 'accepted'
        REJECTED = 'rejected', 'rejected'
        WITHDRAWN = 'withdrawn', 'withdrawn'

    item = models.ForeignKey(LoanItem, on_delete=models.CASCADE, related_name='requests')
    requester_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loan_requests')
    message = models.CharField(max_length=280, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['item', 'status']),
            models.Index(fields=['requester_user']),
        ]

    def __str__(self):
        return f'LoanRequest {self.id} -> LoanItem {self.item_id}'
