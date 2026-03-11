from functools import wraps
from django.http import HttpResponseForbidden

def role_required(*roles):
    def deco(view_func):
        @wraps(view_func)
        def _wrap(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Требуется вход")
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                return HttpResponseForbidden("Недостаточно прав")
            return view_func(request, *args, **kwargs)
        return _wrap
    return deco
