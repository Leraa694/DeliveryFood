from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from ..models import Order
from ..forms.order_form import OrderForm

def order_list(request):
    orders = Order.objects.all()
    return render(request, "Delivery/order/order_list.html", {"orders": orders})

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from ..models import Order
from ..forms.order_form import OrderForm


def order_form(request, pk=None):
    """
    Метод для создания или редактирования заказа с обработкой ошибок.
    """
    # Получаем заказ, если указан `pk`, или создаём новый
    order = get_object_or_404(Order, pk=pk) if pk else None
    form = OrderForm(request.POST or None, request.FILES or None, instance=order)

    if request.method == "POST":
        try:
            if form.is_valid():
                # Получаем очищенные данные из формы
                cleaned_data = form.cleaned_data
                user = cleaned_data["user"]
                restaurant = cleaned_data["restaurant"]
                status = cleaned_data["status"]
                additional_notes = cleaned_data.get("additional_notes")

                # Если есть файлы, обрабатываем их
                uploaded_file = request.FILES.get("link_dogovor")

                # Создаём или обновляем объект вручную
                if order:
                    order.user = user
                    order.restaurant = restaurant
                    order.status = status
                    order.additional_notes = additional_notes
                    if uploaded_file:
                        order.link_dogovor = uploaded_file
                else:
                    order = Order(
                        user=user,
                        restaurant=restaurant,
                        status=status,
                        additional_notes=additional_notes,
                        link_dogovor=uploaded_file,
                    )
                order.save()

                messages.success(request, "Заказ успешно сохранён!")
                return redirect("order_list")  # Перенаправляем на список заказов
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
        except Exception as e:
            messages.error(request, f"Произошла ошибка: {str(e)}")
            return render(request, "Delivery/order/order_form.html", {"form": form})

    return render(request, "Delivery/order/order_form.html", {"form": form})



def order_confirm_delete(request, pk):
    """
    Подтверждение удаления заказа.
    """
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        order.delete()
        messages.success(request, "Заказ успешно удалён.")
        return HttpResponseRedirect(reverse("order_list"))
    return render(request, "Delivery/order/order_confirm_delete.html", {"object": order})

