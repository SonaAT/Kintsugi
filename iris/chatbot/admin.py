from django.contrib import admin
from .models import PanicAttackEntry, DailyMoodEntry

# Register your models here.
class PanicAdmin(admin.ModelAdmin):
    list_display = ("user", "trigger", "timestamp")
class MoodAdmin(admin.ModelAdmin):
    list_display = ("user", "mood", "timestamp")

admin.site.register(PanicAttackEntry, PanicAdmin)
admin.site.register(DailyMoodEntry, MoodAdmin)

