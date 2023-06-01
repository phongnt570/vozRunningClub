from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("top-donates/", views.top_donates, name="top-donates"),
    path("about/", views.about, name="about"),

    path("update-leaderboard/", views.update, name="update-leaderboard"),
    path("upload/", views.upload_file, name="upload"),
]
