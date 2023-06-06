from social_django.models import UserSocialAuth


def get_strava_profile(user):
    try:
        return user.social_auth.get(provider="strava")
    except UserSocialAuth.DoesNotExist:
        return None
