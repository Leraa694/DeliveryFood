from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.auth_views import (
    AuthViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
)
from .views.user_views import UserViewSet
from .views.restaurant_views import RestaurantViewSet, MenuItemViewSet
from .views.order_views import OrderViewSet, OrderMenuItemViewSet
from .views.courier_views import CourierViewSet, DeliveryViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("restaurants", RestaurantViewSet, basename="restaurant")
router.register("menu-items", MenuItemViewSet, basename="menuitem")
router.register("orders", OrderViewSet, basename="order")
router.register("auth", AuthViewSet, basename="auth")
router.register("courier", CourierViewSet, basename="courier")
router.register("delivery", DeliveryViewSet, basename="delivery")
router.register("order-menu-items", OrderMenuItemViewSet, basename="order-menu-items")


urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
]
