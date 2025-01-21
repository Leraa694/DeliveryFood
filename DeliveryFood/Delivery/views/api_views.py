from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction

from ..models import Order, OrderItem, MenuItem

@login_required
@require_http_methods(["POST"])
def add_order_item(request):
    """Добавление позиции в заказ"""
    try:
        menu_item_id = request.POST.get('menu_item_id')
        quantity = int(request.POST.get('quantity', 1))
        order_id = request.POST.get('order_id')

        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        order = get_object_or_404(Order, id=order_id, user=request.user)

        with transaction.atomic():
            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                price=menu_item.price
            )
            order.update_total_price()

        return JsonResponse({
            'status': 'success',
            'item_id': order_item.id,
            'total': float(order.total_price)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def update_order_item(request, item_id):
    """Обновление количества позиции в заказе"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

        with transaction.atomic():
            order_item.quantity = quantity
            order_item.save()
            order_item.order.update_total_price()

        return JsonResponse({
            'status': 'success',
            'total': float(order_item.order.total_price)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def delete_order_item(request, item_id):
    """Удаление позиции из заказа"""
    try:
        order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
        order = order_item.order

        with transaction.atomic():
            order_item.delete()
            order.update_total_price()

        return JsonResponse({
            'status': 'success',
            'total': float(order.total_price)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
