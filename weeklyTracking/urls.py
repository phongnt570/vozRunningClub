from django.urls import path

from . import views

urlpatterns = [
    path("", views.leaderboard, name="index"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("top-donates/", views.top_donates, name="top-donates"),
    # path("about/", views.about, name="about"),

    path("update-leaderboard/", views.post_update_leaderboard, name="update-leaderboard"),
    # path("upload/", views.upload_file, name="upload"),

    path("registration/", views.registration, name="registration"),
    path("join-challenge/", views.join_challenge, name="join-challenge"),

    path("update-after-reg/", views.update_after_registration, name="update-after-registration"),

    path("forget-strava/", views.forget_strava, name="forget-strava"),
]
