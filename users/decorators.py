from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            profile = request.user.profile

            if profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request,"Access Denied")
            return redirect("landing")

        return wrapper
    return decorator