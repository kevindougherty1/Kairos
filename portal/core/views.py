from django.shortcuts import render


def home(request):
    """Placeholder home page for the skeleton. The real public pages replace it on Sunday."""
    return render(request, "core/home.html")
