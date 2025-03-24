from django.urls import path
from . import views

urlpatterns = [
    path("save_trigger/", views.save_trigger, name="save_trigger"),
    path("save_mood/", views.save_mood, name="save_mood"),
    path("get_user/", views.get_logged_in_user, name="get_user"),
]
