from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_cities')
    city = models.CharField(max_length=100)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'city', 'country_code']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city}, {self.country_code}"

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_searches')
    city = models.CharField(max_length=100)
    temperature = models.FloatField(null=True, blank=True)
    conditions = models.CharField(max_length=100, null=True, blank=True)
    icon = models.CharField(max_length=10, null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-searched_at']