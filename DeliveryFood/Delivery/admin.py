from django.contrib import admin
from .models import User, Restaurant, MenuItem, Order, TypeCuisine, OrderDetail, Courier, Delivery
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.utils.html import format_html
from django.urls import reverse
from simple_history.admin import SimpleHistoryAdmin


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ('menu_item_link', 'quantity', 'price')
    fields = ('menu_item_link', 'quantity', 'price')

    def menu_item_link(self, obj):
        if obj.menu_item:
            app_label = obj.menu_item._meta.app_label
            model_name = obj.menu_item._meta.model_name
            link = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.menu_item.id])
            return format_html('<a href="{}">{}</a>', link, obj.menu_item.name)
        return "Нет данных"
    menu_item_link.short_description = 'Блюдо'


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        fields = ('id', 'user__username', 'restaurant__name', 'order_date', 'total_price', 'status')

    def get_export_queryset(self, queryset, *args, **kwargs):
        return queryset.filter(status='completed')

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


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = OrderResource
    list_display = ('id', 'user_link', 'restaurant', 'order_date', 'total_price', 'status', 'order_details_count')
    list_filter = ('status', 'restaurant')
    search_fields = ('user__username', 'restaurant__name')
    date_hierarchy = 'order_date'
    inlines = [OrderDetailInline]
    raw_id_fields = ('user', 'restaurant')
    readonly_fields = ('total_price',)
    list_display_links = ('id', 'user_link')

    def user_link(self, obj):
        app_label = obj.user._meta.app_label
        model_name = obj.user._meta.model_name
        link = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)
    user_link.short_description = 'Пользователь'

    @admin.display(description='Количество позиций')
    def order_details_count(self, obj):
        return obj.order_details.count()

    def get_export_queryset(self, request):
        return super().get_queryset(request).filter(status='completed')


@admin.register(MenuItem)
class MenuItemAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'price', 'is_available', 'restaurant_link')
    list_filter = ('is_available', 'restaurant')
    search_fields = ('name', 'description')

    def restaurant_link(self, obj):
        app_label = obj.restaurant._meta.app_label
        model_name = obj.restaurant._meta.model_name
        link = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', link, obj.restaurant.name)
    restaurant_link.short_description = 'Ресторан'

@admin.register(TypeCuisine)
class TypeCusineAdmin(admin.ModelAdmin):
    list_display = ('cuisine_type',)  # Отображаем тип кухни и количество ресторанов
    search_fields = ('cuisine_type',)  # Поиск по названию типа кухни
    list_filter = ('cuisine_type',)  # Фильтр по типу кухни (если добавите дополнительные поля)
    ordering = ('cuisine_type',)  # Сортировка по названию типа кухни

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'get_cuisines')  # Добавляем отображение типов кухни
    search_fields = ('name', 'phone')  # Расширяем поиск по телефону
    list_filter = ('restaurant',)  # Фильтр по типам кухни
    filter_horizontal = ('restaurant',)  # Удобный выбор типов кухни

    # Метод для отображения связанных типов кухни
    def get_cuisines(self, obj):
        return ", ".join([cuisine.cuisine_type for cuisine in obj.restaurant.all()])
    get_cuisines.short_description = "Типы кухни"


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    readonly_fields = ('last_login', 'date_joined')
    list_display_links = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

@admin.register(Courier)
class CourierAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'vehicle_type')
    list_filter = ('vehicle_type',)


@admin.register(Delivery)
class DeliveryAdmin(SimpleHistoryAdmin):
    list_display = ('order', 'courier', 'delivery_time', 'delivery_status')
    list_filter = ('delivery_status',)
    search_fields = ('order__id', 'courier__user__username')


admin.site.register(OrderDetail)