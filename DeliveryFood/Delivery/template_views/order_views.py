from django.shortcuts import render, get_object_or_404, redirect
from ..models import Order
from ..forms.order_form import OrderForm

def order_list(request):
    orders = Order.objects.all()
    return render(request, "Delivery/order/order_list.html", {"orders": orders})

def order_form(request, pk=None):
    if pk:
        order = get_object_or_404(Order, pk=pk)
    else:
        order = None
    form = OrderForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("order_list")
    return render(request, "Delivery/order/order_form.html", {"form": form})

def order_confirm_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        order.delete()
        return redirect("order_list")
    return render(request, "Delivery/order/order_confirm_delete.html", {"object": order})
