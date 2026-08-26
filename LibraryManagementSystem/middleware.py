from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited

class RateLimit429Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            return HttpResponse(
                "<h1>429 Too Many Requests</h1><p>Rate limit exceeded. Please wait before trying again.</p>",
                status=429
            )
        return None