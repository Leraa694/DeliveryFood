from django.contrib import admin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile
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
    actions = ["export_as_pdf"]

    def export_as_pdf(self, request, queryset):
        """Генерация PDF для выбранных заказов."""
        orders = queryset
        html_string = render_to_string("Delivery/admin/orders_pdf_template.html", {"orders": orders})
        html = HTML(string=html_string)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            html.write_pdf(target=tmp_file.name)
            with open(tmp_file.name, "rb") as pdf:
                response = HttpResponse(pdf.read(), content_type="application/pdf")
                response["Content-Disposition"] = "inline; filename=orders.pdf"
                return response

    export_as_pdf.short_description = "Экспортировать в PDF"



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
