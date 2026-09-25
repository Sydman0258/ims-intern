from django.contrib.auth import login,logout
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import EmailAuthenticationForm
from .models import Role


class LoginView(FormView):
    """Class-based login that also issues JWT cookies on success."""

    template_name = "accounts/login.html"
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy("accounts:login")  # overridden after login
    redirect_authenticated_user=True
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect_by_role(request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response=super().form_valid(form)
        user = form.get_user()
        login(self.request, user)
        return response
        # Issue JWT cookies so API / SPA clients are also authenticated
        # from .jwt_views import _tokens_for_user, _set_jwt_cookies

        # tokens = _tokens_for_user(user)
        # response = redirect_by_role(user)  # HttpResponseRedirect
        # return _set_jwt_cookies(response, tokens["access"], tokens["refresh"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class LogoutView(DjangoLogoutView):
    """Logout and clear JWT cookies."""

    next_page = reverse_lazy("accounts:login")
    def get(self,request):
        logout(request)
        return redirect("/")
#     def dispatch(self, request, *args, **kwargs):
#         response = super().dispatch(request, *args, **kwargs)
#         # from .jwt_views import _clear_jwt_cookies
#         return _clear_jwt_cookies(response)


def redirect_by_role(user):
    if user.role == Role.ADMIN:
        return redirect("/admin/")
    if user.role == Role.TENANT:
        return redirect("tenant:dashboard")
    if user.role == Role.MALL_MANAGER:
        return redirect("mall:index")
    return redirect("accounts:login")
