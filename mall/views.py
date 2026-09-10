from django.shortcuts import render
from .models import Mall


def index(request):
    malls = Mall.objects.order_by("-created_at")[:5]
    return render(request, "mall/index.html", {"malls": malls})