from django import template
from ..models import Order

register = template.Library()

@register.simple_tag
def greeting():
    """Простой шаблонный тег, возвращающий текст."""
    return "Добро пожаловать в систему заказов!"

@register.simple_tag
def calculate_total(price, quantity):
    """Шаблонный тег, который рассчитывает итоговую стоимость."""
    return price * quantity

@register.simple_tag
def recent_orders(count=5):
    """Шаблонный тег, возвращающий последние заказы."""
    return Order.objects.order_by('-order_date')[:count]
