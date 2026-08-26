import time
from django.core.cache import cache
from django.http import JsonResponse

class RateLimit429Middleware:
    """
    Limits requests per IP address for API endpoints.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Apply rate limiting specifically to the book API endpoints
        if request.path.startswith('/books/api/'):
            # Identify user by IP address (or user ID if logged in)
            client_ip = request.META.get('REMOTE_ADDR')
            cache_key = f"rate_limit_{client_ip}"

            # Set limit: Max 5 requests per 10 seconds
            RATE_LIMIT = 5
            TIME_WINDOW = 10  # in seconds

            # Get request history from Django cache
            request_history = cache.get(cache_key, [])
            now = time.time()

            # Remove requests outside the current time window
            request_history = [t for t in request_history if now - t < TIME_WINDOW]

            if len(request_history) >= RATE_LIMIT:
                return JsonResponse(
                    {"error": "Too Many Requests. Please slow down."},
                    status=429
                )

            # Record current request timestamp and update cache
            request_history.append(now)
            cache.get_or_set(cache_key, request_history, TIME_WINDOW)

        return self.get_response(request)