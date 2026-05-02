import zoneinfo

from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                tz = zoneinfo.ZoneInfo(request.user.profile.timezone)
                timezone.activate(tz)
            except (AttributeError, zoneinfo.ZoneInfoNotFoundError):
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Referrer-Policy', 'same-origin')
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
        response.setdefault('X-Content-Type-Options', 'nosniff')
        return response
