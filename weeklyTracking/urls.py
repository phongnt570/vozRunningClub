from django.contrib.auth import views as auth_views
from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.leaderboard, name="index"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("top-donates/", views.top_donates, name="top-donates"),
    # path("about/", views.about, name="about"),

    # path("update-leaderboard/", views.post_update_leaderboard, name="update-leaderboard"),
    # # path("upload/", views.upload_file, name="upload"),
    #
    path("registration/", views.registration, name="registration"),
    path("weekly-registration/", views.weekly_registration, name="weekly-registration"),

    path("update-profile/", views.update_profile, name="update-profile"),
    path("update-strava/", views.update_strava, name="update-strava"),


    path("disconnect-strava/", views.disconnect_strava, name="disconnect-strava"),

    path("oauth/", include("social_django.urls", namespace="social")),
    path("profile/", views.profile, name="profile"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
