from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views.generic import FormView

from .forms import EmailAuthenticationForm
from .models import Role


class LoginView(FormView):
    template_name="accounts/login.html"
    form_class=EmailAuthenticationForm

    def get_from_kwargs(self):
        self.kwargs=super().get_from_kwargs()
        self.kwargs["request"]=self.request
        return self.kwargs

    def form_valid(self,form):
       user=form.get_user()
       login(self.request,user)
       return redirect_by_role(user)

    def form_invalid(self,form):
       return super().form_invalid(form)


def redirect_by_role(user):
        if user.role == Role.ADMIN:
         return redirect("/admin/")
        if user.role == Role.TENANT:
         return redirect("tenant:dashboard")
        if user.role == Role.MALL_MANAGER:
         return redirect("mall:index")
        return redirect("accounts:login")
