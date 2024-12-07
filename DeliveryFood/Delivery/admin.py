from django.contrib import admin
from .models import User, Restaurant, MenuItem, Order, TypeCuisine, OrderMenuItem, Courier, Delivery
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.utils.html import format_html
from import_export.formats.base_formats import XLSX, CSV, JSON
from django.urls import reverse
from simple_history.admin import SimpleHistoryAdmin
from .resources import CompletedOrderResource, MenuItemResource, UserResource

class OrderMenuItemInline(admin.TabularInline):
    model = OrderMenuItem
    extra = 1
    fields = ('menu_item', 'quantity', 'price')
    readonly_fields = ('price',)

    @admin.display(description='Цена')
    def price(self, obj):
        return obj.price if obj.id else "-"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "menu_item":
            # Получаем ID заказа из текущего URL
            order_id = request.resolver_match.kwargs.get("object_id")
            if order_id:
                try:
                    # Находим заказ и фильтруем меню по ресторану
                    order = Order.objects.get(pk=order_id)
                    kwargs["queryset"] = MenuItem.objects.filter(restaurant=order.restaurant)
                except Order.DoesNotExist:
                    pass
            else:
                # Если заказ еще не сохранен, показываем пустой QuerySet
                kwargs["queryset"] = MenuItem.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = CompletedOrderResource
    list_display = ('id', 'user_link', 'restaurant', 'order_date', 'total_price', 'status', 'order_items_count')
    list_filter = ('status', 'restaurant')
    search_fields = ('user__username', 'restaurant__name')
    date_hierarchy = 'order_date'
    inlines = [OrderMenuItemInline]
    raw_id_fields = ('user', 'restaurant')
    readonly_fields = ('total_price',)
    list_display_links = ('id', 'user_link')

    def get_export_formats(self):
        return [XLSX, CSV, JSON]

    def save_related(self, request, form, formsets, change):
        """Пересчет общей стоимости после сохранения связанных объектов."""
        super().save_related(request, form, formsets, change)
        form.instance.update_total_price()

    def user_link(self, obj):
        app_label = obj.user._meta.app_label
        model_name = obj.user._meta.model_name
        link = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)
    user_link.short_description = 'Пользователь'

    @admin.display(description='Количество позиций')
    def order_items_count(self, obj):
        return obj.order_items.count()

    def get_export_queryset(self, request):
        return super().get_queryset(request).filter(status='completed')


@admin.register(MenuItem)
class MenuItemAdmin(SimpleHistoryAdmin):
    resource_class = MenuItemResource
    list_display = ('name', 'price', 'is_available', 'restaurant_link')
    list_filter = ('is_available', 'restaurant')
    search_fields = ('name', 'description')

    def get_export_formats(self):
        return [XLSX, CSV, JSON]

    def restaurant_link(self, obj):
        app_label = obj.restaurant._meta.app_label
        model_name = obj.restaurant._meta.model_name
        link = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', link, obj.restaurant.name)
    restaurant_link.short_description = 'Ресторан'


@admin.register(TypeCuisine)
class TypeCuisineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'get_cuisines')
    search_fields = ('name', 'phone')
    list_filter = ('name',)  # Используйте существующие поля

    def get_cuisines(self, obj):
        return ", ".join([cuisine.name for cuisine in obj.cuisine_types.all()])
    get_cuisines.short_description = "Типы кухни"


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):
    resource_class = UserResource
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
