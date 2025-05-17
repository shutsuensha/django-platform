from django.contrib.auth.models import User
from django.db import models


class Ad(models.Model):
    CONDITION_CHOICES = [
        ("new", "Новый"),
        ("used", "Б/у"),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ads")
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="ads_images/", blank=True, null=True)
    category = models.CharField(max_length=100)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ExchangeProposal(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("accepted", "Принята"),
        ("rejected", "Отклонена"),
    ]

    id = models.BigAutoField(primary_key=True)
    ad_sender = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="sent_proposals")
    ad_receiver = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="received_proposals")
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Предложение обмена от '{self.ad_sender}' к '{self.ad_receiver}' [{self.get_status_display()}]"
