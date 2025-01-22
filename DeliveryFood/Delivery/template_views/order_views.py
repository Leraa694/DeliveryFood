from django.http import HttpResponseRedirect
from django.urls import reverse
from ..forms.order_form import OrderForm, OrderItemFormSet

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from ..models import Order


def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES)
        formset = OrderItemFormSet(request.POST, instance=Order())  # instance=Order(), т.к. заказа ещё нет
        if form.is_valid() and formset.is_valid():
            # Сохраняем сам заказ
            order = form.save(commit=False)
            order.save()
            # Теперь привязываем formset к сохранённому заказу и сохраняем
            formset.instance = order
            formset.save()
            return redirect(reverse("order_detail", args=[order.id]))
    else:
        form = OrderForm()
        formset = OrderItemFormSet(instance=Order())  # Пустой заказ
    return render(request, "Delivery/order/order_create.html", {"form": form, "formset": formset})



def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()          # Сохраняем сам заказ
            formset.save()       # Сохраняем позиции заказа
            return redirect(reverse("order_detail", args=[order.id]))
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    return render(request, "Delivery/order/order_edit.html", {"form": form, "formset": formset, "order": order})

def order_confirm_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        order.delete()
        return redirect("current_orders_list")
    return render(request, "Delivery/order/order_confirm_delete.html", {"order": order})


