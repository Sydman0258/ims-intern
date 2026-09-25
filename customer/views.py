from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView, View


class ShopView(TemplateView):

    template_name = "customer/shop.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["online_disabled"] = True
        return ctx


class PurchaseView(View):
    def get(self, request, product_id):
        messages.info(
            request, "Online purchasing is not available. Please visit the store."
        )
        return redirect("customer:index")

    def post(self, request, product_id):
        return self.get(request, product_id)


class PurchaseDetailView(View):
    def get(self, request, pk):
        messages.info(request, "Online purchasing is not available.")
        return redirect("customer:index")
