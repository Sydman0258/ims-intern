from django.conf import settings
from django.db import models



class Mall(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mall_profile",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, unique=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    floors = models.IntegerField()
    total_shops = models.IntegerField()
    num_leased = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

