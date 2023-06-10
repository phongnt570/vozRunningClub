from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from social_core.exceptions import AuthAlreadyAssociated, AuthCanceled
from social_django.middleware import SocialAuthExceptionMiddleware


class StravaAuthAlreadyAssociatedMiddleware(SocialAuthExceptionMiddleware):
    """Redirect users to Profile page when AuthAlreadyAssociated exception occurs."""

    def process_exception(self, request, exception):
        if request.backend.name == "strava":
            if isinstance(exception, AuthAlreadyAssociated):
                messages.error(request, "Strava account already associated with another account.")
                return redirect(reverse("profile"))
            if isinstance(exception, AuthCanceled):
                messages.error(request, "Strava authentication canceled.")
                return redirect(reverse("registration"))
            else:
                messages.error(request, "Strava authentication failed.")
                return redirect(reverse("registration"))
