from django.urls import path
from .template_views import order_views
from .template_views.home_views import *
from .template_views.order_views import *

urlpatterns = [
    # Существующие URL'ы
    path("orders/create/", order_create, name="order_create"),
    path("orders/<int:pk>/edit/", order_edit, name="order_edit"),
    path("orders/<int:pk>/delete/", order_confirm_delete, name="order_confirm_delete"),

    # Главная
    path("", home, name="home"),

    # Поиск
    path("search/", search, name="search"),

    # Топ-страницы
    path("top-restaurants/", top_restaurants_list, name="top_restaurants_list"),
    path("popular-dishes/", popular_dishes_list, name="popular_dishes_list"),
    path("current-orders/", current_orders_list, name="current_orders_list"),

    # Детальные страницы
    path("restaurant/<int:pk>/", restaurant_detail, name="restaurant_detail"),
    path("dish/<int:pk>/", dish_detail, name="dish_detail"),
    path("order/<int:pk>/", order_detail, name="order_detail"),
]
