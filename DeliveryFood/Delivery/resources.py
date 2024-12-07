# resources.py

from import_export import resources
from .models import Order, User, MenuItem


class CompletedOrderResource(resources.ModelResource):
    class Meta:
        model = Order
        fields = ('id', 'user__username', 'restaurant__name', 'order_date', 'total_price', 'status')
        export_order = ('id', 'user__username', 'restaurant__name', 'order_date', 'total_price', 'status')

    def dehydrate_status(self, order):
        status_mapping = {
            'new': 'Новый',
            'preparing': 'Готовится',
            'delivering': 'Доставляется',
            'completed': 'Завершен',
        }
        return status_mapping.get(order.status, 'Неизвестный статус')

    def dehydrate_user(self, order):
        return f"{order.user.first_name} {order.user.last_name} ({order.user.username})"


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role')

    def dehydrate_role(self, user):
        role_mapping = dict(User.ROLES)
        return role_mapping.get(user.role, 'Неизвестная роль')


class MenuItemResource(resources.ModelResource):
    class Meta:
        model = MenuItem
        fields = ('id', 'name', 'price', 'is_available', 'restaurant__name')
        export_order = ('id', 'name', 'price', 'is_available', 'restaurant__name')

    def dehydrate_is_available(self, menu_item):
        return 'Доступно' if menu_item.is_available else 'Не доступно'