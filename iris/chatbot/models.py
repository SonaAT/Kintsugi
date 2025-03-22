from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class PanicAttackEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trigger = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class DailyMoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=255)  # Can store mood as a text like "Happy", "Anxious", etc.
    timestamp = models.DateTimeField(auto_now_add=True)
