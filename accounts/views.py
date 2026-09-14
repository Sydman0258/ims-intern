from django.contrib.auth import login
from django.shortcuts import render, redirect

from .forms import EmailAuthenticationForm
from .models import Role


def login_view(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect_by_role(form.get_user())
        return render(request, "accounts/login.html", {"form": form})

    form = EmailAuthenticationForm(request=request)
    return render(request, "accounts/login.html", {"form": form})


def redirect_by_role(user):
    if user.role == Role.ADMIN:
        return redirect("/admin/")
    if user.role == Role.TENANT:
        return redirect("tenant:dashboard")
    if user.role == Role.MALL:
        return redirect("mall:index")
    return redirect("customer:index")