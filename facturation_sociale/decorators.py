from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def acces_cabinet(view):
    """Réserve une vue au personnel du cabinet (is_staff ou is_superuser)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect("access_denied")
        return view(request, *args, **kwargs)

    return wrapper
