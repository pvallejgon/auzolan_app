from django.conf import settings
from django.db import models
from apps.requests.models import Request


class Report(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'open'
        IN_REVIEW = 'in_review', 'in_review'
        CLOSED = 'closed', 'closed'

    class Reason(models.TextChoices):
        PAYMENTS = 'payments', 'payments'
        ADVERTISING = 'advertising', 'advertising'
        PROHIBITED_CONTENT = 'prohibited_content', 'prohibited_content'
        HARASSMENT = 'harassment', 'harassment'
        OTHER = 'other', 'other'

    reporter_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    reason = models.CharField(max_length=40, choices=Reason.choices)
    description = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Report {self.id}'
