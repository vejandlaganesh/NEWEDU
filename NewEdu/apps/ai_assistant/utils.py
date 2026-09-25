from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse
import time

def rate_limit_ai_request(func):
    """
    Decorator to rate limit AI API requests per user.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
            
        # Configurable limit: default 10 requests per minute
        LIMIT = getattr(settings, 'AI_RATE_LIMIT', 10)
        WINDOW = getattr(settings, 'AI_RATE_LIMIT_WINDOW', 60)
        
        cache_key = f"ai_ratelimit_{request.user.id}"
        
        # We will store a list of timestamps
        request_times = cache.get(cache_key, [])
        current_time = time.time()
        
        # Remove timestamps older than WINDOW
        request_times = [t for t in request_times if current_time - t < WINDOW]
        
        if len(request_times) >= LIMIT:
            return JsonResponse(
                {'error': 'Too many requests. Please wait a moment before trying again.'},
                status=429
            )
            
        request_times.append(current_time)
        cache.set(cache_key, request_times, WINDOW)
        
        return func(request, *args, **kwargs)
    return wrapper
