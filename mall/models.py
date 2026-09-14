from django.db import models



class Mall(models.Model):
    name = models.CharField(max_length=100, unique=True)
    floors = models.IntegerField()
    total_shops = models.IntegerField()
    num_leased = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

