from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("update-leaderboard/", views.update, name="update-leaderboard"),
]
