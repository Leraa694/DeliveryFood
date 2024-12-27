from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import MenuItem, OrderMenuItem


@receiver(post_save, sender=OrderMenuItem)
@receiver(post_delete, sender=OrderMenuItem)
def update_order_total_price(sender, instance, **kwargs):
    """Обновляет общую стоимость заказа при изменении позиций."""
    order = instance.order
    order.update_total_price()
    order.save()


@receiver(post_save, sender=MenuItem)
def update_related_orders_on_menuitem_change(sender, instance, **kwargs):
    """Обновляет общую стоимость заказов при изменении цены блюда."""
    related_order_items = OrderMenuItem.objects.filter(menu_item=instance)
    orders = set(item.order for item in related_order_items)
    for order in orders:
        order.update_total_price()
        order.save()
