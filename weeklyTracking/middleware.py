from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from social_core.exceptions import AuthAlreadyAssociated
from social_django.middleware import SocialAuthExceptionMiddleware


class StravaAuthAlreadyAssociatedMiddleware(SocialAuthExceptionMiddleware):
    """Redirect users to Profile page when AuthAlreadyAssociated exception occurs."""

    def process_exception(self, request, exception):
        if isinstance(exception, AuthAlreadyAssociated):
            if request.backend.name == "strava":
                messages.error(request, "Strava account already associated with another account.")
                return redirect(reverse("profile"))
