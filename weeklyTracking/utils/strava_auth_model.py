from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from weeklyTracking.models import SettingStravaClub, UserProfile


def get_strava_profile(user: User) -> UserSocialAuth:
    try:
        return user.social_auth.get(provider="strava")
    except UserSocialAuth.DoesNotExist:
        return None


def check_strava_connection(user: User) -> bool:
    strava_connected = True

    strava_profile = get_strava_profile(user)

    if not strava_profile:
        strava_connected = False
    else:
        try:
            strategy = load_strategy()
            access_token = strava_profile.get_access_token(strategy)
            backend = strava_profile.get_backend_instance(strategy)
            user_details = backend.user_data(access_token=access_token)

            user.first_name = user_details.get("firstname", "")
            user.last_name = user_details.get("lastname", "")
            user.save()
        except Exception:
            strava_connected = False

    if not strava_connected:
        if strava_profile:
            strava_profile.set_extra_data({})
            strava_profile.save()

    return strava_connected


def check_strava_club_joined(user: User, save: bool = True) -> bool:
    joined = False

    user_profile = UserProfile.objects.get_or_create(user=user)[0]

    if check_strava_connection(user):
        strava_profile = get_strava_profile(user)
        strava_club_url = SettingStravaClub.objects.get().club_url
        strava_club_id = int(strava_club_url.split("/")[-1])

        try:
            strategy = load_strategy()
            access_token = strava_profile.get_access_token(strategy)
            backend = strava_profile.get_backend_instance(strategy)
            user_clubs = backend.get_json(
                "https://www.strava.com/api/v3/athlete/clubs",
                params={"access_token": access_token},
            )
            for club in user_clubs:
                if club["id"] == strava_club_id:
                    joined = True
                    break
        except Exception:
            pass

    if save:
        user_profile.strava_club_joined = joined
        user_profile.save()

    return joined
