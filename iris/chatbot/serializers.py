from rest_framework import serializers
from .models import PanicAttackEntry, DailyMoodEntry

class PanicAttackEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PanicAttackEntry
        fields = ['user', 'trigger', 'timestamp']

class DailyMoodEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMoodEntry
        fields = ['user', 'mood', 'timestamp']
