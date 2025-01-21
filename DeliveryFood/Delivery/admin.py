from django.contrib import admin
from .models import (
    User,
    Restaurant,
    MenuItem,
    Order,
    TypeCuisine,
    OrderMenuItem,
    Courier,
    Delivery,
)
from import_export.admin import ExportMixin
from django.utils.html import format_html
from django.urls import reverse
from simple_history.admin import SimpleHistoryAdmin


class OrderMenuItemInline(admin.TabularInline):
    model = OrderMenuItem
    extra = 1
    fields = ("menu_item", "quantity", "price")
    readonly_fields = ("price",)

    @admin.display(description="Цена")
    def price(self, obj):
        return obj.price if obj.id else "-"


@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin, ExportMixin):
    list_display = (
        "id",
        "user_link",
        "restaurant",
        "order_date",
        "total_price",
        "status",
        "link_dogovor",
    )
    list_filter = ("status", "restaurant")
    search_fields = ("user__username", "restaurant__name")
    date_hierarchy = "order_date"
    inlines = [OrderMenuItemInline]
    readonly_fields = ("total_price",)

    def save_related(self, request, form, formsets, change):
        """Пересчет общей стоимости после сохранения связанных объектов."""
        super().save_related(request, form, formsets, change)
        form.instance.update_total_price()

    def user_link(self, obj):
        """Ссылка на пользователя в админке."""
        link = reverse(
            f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change",
            args=[obj.user.id],
        )
        return format_html('<a href="{}">{}</a>', link, obj.user.username)

    user_link.short_description = "Пользователь"


@admin.register(MenuItem)
class MenuItemAdmin(SimpleHistoryAdmin, ExportMixin):
    list_display = ("name", "price", "is_available", "restaurant")
    list_filter = ("is_available", "restaurant")
    search_fields = ("name", "description")


@admin.register(TypeCuisine)
class TypeCuisineAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "get_cuisines")
    search_fields = ("name", "phone")

    def get_cuisines(self, obj):
        return ", ".join([c.name for c in obj.cuisine_types.all()])

    get_cuisines.short_description = "Типы кухни"


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")
    readonly_fields = ("last_login", "date_joined")


@admin.register(Courier)
class CourierAdmin(SimpleHistoryAdmin):
    list_display = ("user", "vehicle_type")
    list_filter = ("vehicle_type",)


@admin.register(Delivery)
class DeliveryAdmin(SimpleHistoryAdmin):
    list_display = ("order", "courier", "delivery_time", "delivery_status")
    list_filter = ("delivery_status",)
    search_fields = ("order__id", "courier__user__username")
