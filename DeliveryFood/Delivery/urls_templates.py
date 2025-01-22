from django.urls import path
from .template_views import order_views, restaurants_views
from .views.home_views import (
    home,
    top_restaurants_list,
    popular_dishes_list,
    current_orders_list,
    restaurant_detail,
    dish_detail,
    order_detail,
    search
)

urlpatterns = [
    # Существующие URL'ы
    path("orders/", order_views.order_list, name="order_list"),
    path("orders/new/", order_views.order_form, name="order_new"),
    path("orders/<int:pk>/edit/", order_views.order_form, name="order_edit"),
    path("orders/<int:pk>/delete/", order_views.order_confirm_delete, name="order_confirm_delete"),
    path("restaurants/", restaurants_views.restaurant_list, name="restaurants"),

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
