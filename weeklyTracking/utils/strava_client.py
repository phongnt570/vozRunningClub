from django.conf import settings


def get_strava_client_id():
    return settings.SOCIAL_AUTH_STRAVA_KEY


def get_strava_client_secret():
    return settings.SOCIAL_AUTH_STRAVA_SECRET
