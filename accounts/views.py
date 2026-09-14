# accounts/views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Role


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect_by_role(user)

        return render(request, "accounts/login.html", {"error": "Invalid email or password"})

    return render(request, "accounts/login.html")


def redirect_by_role(user):
    if user.role == Role.ADMIN:
        return redirect("/admin/")
    if user.role == Role.TENANT:
        return redirect("tenant:dashboard")
    if user.role == Role.MALL:
        return redirect("mall:index")
    return redirect("customer:index")