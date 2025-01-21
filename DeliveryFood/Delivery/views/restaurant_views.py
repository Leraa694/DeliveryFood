from datetime import timedelta

from rest_framework import viewsets, permissions, filters, status as status_code
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db.models import Q, Avg, Count
from rest_framework.decorators import action
from ..models import Restaurant, MenuItem
from ..serializers.restaurant_serializers import (
    RestaurantSerializer,
    MenuItemSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """
    Кастомная пагинация для стандартного набора результатов.
    """

    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = (
        "page_size"  # Параметр для задания размера страницы через запрос
    )
    max_page_size = 100  # Максимальное количество элементов на странице

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "address"]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(operation_summary="Получить список ресторанов")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.prefetch_related("cuisine_types")  # Оптимизация
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Получить рестораны по типу кухни",
        manual_parameters=[
            openapi.Parameter(
                "cuisine_type",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Тип кухни",
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="by-cuisine-type")
    def restaurants_by_cuisine_type(self, request):
        """
        Возвращает рестораны, которые предлагают определённый тип кухни.
        """
        cuisine_type = request.query_params.get("cuisine_type")
        if not cuisine_type:
            return Response(
                {"error": "Параметр 'cuisine_type' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        restaurants = self.queryset.filter(cuisine_types__name__icontains=cuisine_type)
        restaurants = restaurants.prefetch_related("cuisine_types")  # Оптимизация
        page = self.paginate_queryset(restaurants)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(restaurants, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Получить статистику блюд по ресторанам")
    @action(methods=["GET"], detail=False, url_path="menu-stats")
    def menu_stats(self, request):
        """
        Возвращает количество блюд и среднюю цену по каждому ресторану.
        """
        stats = (
            MenuItem.objects.values("restaurant__id", "restaurant__name")
            .annotate(
                total_items=Count("id"),
                average_price=Avg("price"),
            )
            .order_by("-total_items")
        )
        return Response(stats)


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related("restaurant").all()  # Оптимизация
    serializer_class = MenuItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(operation_summary="Получить список блюд")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.select_related("restaurant")  # Оптимизация
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Получить среднюю цену и количество блюд")
    @action(methods=["GET"], detail=False, url_path="aggregated-stats")
    def aggregated_stats(self, request):
        """
        Возвращает статистику: средняя цена и общее количество блюд.
        """
        stats = self.queryset.aggregate(
            average_price=Avg("price"), total_items=Count("id")
        )
        return Response(
            {
                "average_price": stats["average_price"],
                "total_items": stats["total_items"],
            }
        )

    @swagger_auto_schema(
        operation_summary="Получить блюда по ресторану",
        manual_parameters=[
            openapi.Parameter(
                "restaurant_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="ID ресторана",
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="by-restaurant")
    def menu_items_by_restaurant(self, request):
        """
        Возвращает блюда определённого ресторана.
        """
        restaurant_id = request.query_params.get("restaurant_id")
        if not restaurant_id:
            return Response(
                {"error": "Параметр 'restaurant_id' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        menu_items = self.queryset.filter(restaurant__id=restaurant_id)
        menu_items = menu_items.select_related("restaurant")  # Оптимизация
        page = self.paginate_queryset(menu_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(menu_items, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Исключить блюда с ценой ниже заданного порога",
        manual_parameters=[
            openapi.Parameter(
                "price_threshold",
                openapi.IN_QUERY,
                type=openapi.TYPE_NUMBER,
                description="Минимальная цена блюда",
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="exclude-low-price")
    def exclude_low_price_items(self, request):
        """
        Исключает блюда с ценой ниже заданного порога.
        """
        price_threshold = request.query_params.get("price_threshold")
        if not price_threshold:
            return Response(
                {"error": "Параметр 'price_threshold' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        try:
            price_threshold = float(price_threshold)
        except ValueError:
            return Response(
                {"error": "Параметр 'price_threshold' должен быть числом."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        filtered_items = self.queryset.exclude(price__lt=price_threshold)
        filtered_items = filtered_items.select_related("restaurant")  # Оптимизация
        page = self.paginate_queryset(filtered_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_items, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Получить названия и цены блюд для ресторана",
        manual_parameters=[
            openapi.Parameter(
                "restaurant_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="ID ресторана",
                required=True,
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="names-and-prices-by-restaurant")
    def names_and_prices_by_restaurant(self, request):
        """
        Возвращает список названий и цен блюд для заданного ресторана.
        """
        restaurant_id = request.query_params.get("restaurant_id")
        if not restaurant_id:
            return Response(
                {"error": "Параметр 'restaurant_id' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        items = self.queryset.filter(restaurant_id=restaurant_id).values_list("name", "price")
        return Response(list(items))
