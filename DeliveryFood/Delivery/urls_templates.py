from django.urls import path
from .template_views import order_views

urlpatterns = [
    path("orders/", order_views.order_list, name="order_list"),
    path("orders/new/", order_views.order_form, name="order_new"),
    path("orders/<int:pk>/edit/", order_views.order_form, name="order_edit"),
    path("orders/<int:pk>/delete/", order_views.order_confirm_delete, name="order_confirm_delete"),
]