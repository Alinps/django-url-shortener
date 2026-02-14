from django.shortcuts import render
from django.conf import settings


def rate_limited_response(request, window_seconds):
    response = render(
        request,
        "rate_limited.html",
        {"retry_after": window_seconds},
        status=429
    )
    response["Retry-After"] = window_seconds
    return response
