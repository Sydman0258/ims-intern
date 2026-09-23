from django.contrib import messages
from django.shortcuts import redirect, render


def shop(request):
    """Online buying is disabled. Customers shop in-store only."""
    return render(request, "customer/shop.html", {"online_disabled": True})


def purchase(request, product_id):
    messages.info(request, "Online purchasing is not available. Please visit the store.")
    return redirect("customer:index")


def purchase_detail(request, pk):
    messages.info(request, "Online purchasing is not available.")
    return redirect("customer:index")
