from rest_framework import viewsets, permissions, filters
from drf_yasg.utils import swagger_auto_schema
from ..models import Restaurant, MenuItem
from ..serializers.restaurant_serializers import RestaurantSerializer, MenuItemSerializer

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address']

    @swagger_auto_schema(operation_summary="Получить список ресторанов")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @swagger_auto_schema(operation_summary="Получить список блюд")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
