from datetime import timedelta

from rest_framework import viewsets, permissions, filters, status as status_code
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import action
from ..models import Order, OrderMenuItem
from django.core.cache import cache
from ..serializers.order_serializers import OrderSerializer, OrderMenuItemSerializer
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter, NumberFilter


# Кастомный класс фильтрации (если нужен)
class OrderFilter(FilterSet):
    restaurant_name = CharFilter(field_name="restaurant__name", lookup_expr="icontains")
    min_price = NumberFilter(field_name="total_price", lookup_expr="gte")
    max_price = NumberFilter(field_name="total_price", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["restaurant_name", "min_price", "max_price"]


class StandardResultsSetPagination(PageNumberPagination):
    """
    Кастомная пагинация для стандартного набора результатов.
    """

    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = (
        "page_size"  # Параметр для задания размера страницы через запрос
    )
    max_page_size = 100  # Максимальное количество элементов на странице


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ["order_date", "total_price"]
    ordering = ["order_date"]

    @swagger_auto_schema(
        operation_summary="Get a list of orders with filters and pagination",
        manual_parameters=[
            openapi.Parameter("restaurant_name", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Restaurant name"),
            openapi.Parameter("min_price", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description="Minimum order price"),
            openapi.Parameter("max_price", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description="Maximum order price"),
            openapi.Parameter("page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Page number"),
            openapi.Parameter("page_size", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Page size"),
            openapi.Parameter("ordering", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Sorting parameter"),
        ],
    )
    def list(self, request, *args, **kwargs):
        """
        Returns a list of orders with filters, pagination, and caching.
        """
        cache_key = f"orders_{request.query_params.urlencode()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status_code.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, timeout=60 * 10)  # Cache for 15 minutes
            return Response(response_data)

        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, timeout=60 * 10)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new order and clear the order list cache.
        """
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            cache.delete_pattern("orders_*")  # Clear all cached order lists
        return response

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update an order and clear related cache.
        """
        instance_id = kwargs.get("pk")
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            cache.delete_pattern("orders_*")
            cache.delete(f"order_{instance_id}")
        return response

    def destroy(self, request, *args, **kwargs):
        """
        Delete an order and clear related cache.
        """
        instance_id = kwargs.get("pk")
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            cache.delete_pattern("orders_*")
            cache.delete(f"order_{instance_id}")
        return response

    @swagger_auto_schema(
        operation_summary="Обновить статус заказа",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый статус заказа ('new', 'preparing', 'delivering', 'completed')",
                )
            },
        ),
        responses={
            200: OrderSerializer(),
            400: openapi.Response("Ошибка валидации данных"),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление заказа (например, изменение статуса).
        """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить заказы определенного пользователя",
        manual_parameters=[
            openapi.Parameter(
                "user_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="ID пользователя",
            ),
        ],
        responses={200: OrderSerializer(many=True)},
    )
    @action(methods=["GET"], detail=False, url_path="by-user")
    def orders_by_user(self, request):
        """
        Возвращает заказы, сделанные определенным пользователем.
        """
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"error": "Параметр 'user_id' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        orders = self.queryset.filter(user__id=user_id)
        page = self.paginate_queryset(orders)  # Применяем пагинацию
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Получить заказы по статусу",
        manual_parameters=[
            openapi.Parameter(
                "status",
                openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="Статус заказа ('new', 'preparing', 'delivering', 'completed')",
                required=True,
            )
        ],
        responses={200: OrderSerializer(many=True)},
    )
    @action(methods=["GET"], detail=False, url_path="status/(?P<status>[\w-]+)")
    def search_by_status(self, request, status=None):
        """
        Возвращает заказы по статусу.
        """
        if not status:
            return Response(
                {"error": "Параметр 'status' обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Фильтруем заказы по статусу
        orders = self.queryset.filter(status=status)
        page = self.paginate_queryset(orders)  # Применяем пагинацию
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    # Функция для выборки заказов по условиям
    def get_orders_for_status_or_time(self):
        one_hour_ago = timezone.now() - timedelta(hours=1)

        # Используем Q для фильтрации
        orders = self.queryset.filter(
            Q(status="preparing")
            | (Q(order_date__lt=one_hour_ago) & ~Q(status="completed"))
        )
        return orders

    @swagger_auto_schema(
        operation_summary="Получить заказы, которые готовятся или старше 1 часа и не доставлены",
        responses={200: OrderSerializer(many=True)},
    )
    @action(methods=["GET"], detail=False, url_path="ready-or-past-due")
    def get_ready_or_past_due_orders(self, request):
        """
        Возвращает заказы, которые готовятся или прошли больше 1 часа и не доставлены.
        """
        orders = self.get_orders_for_status_or_time()
        page = self.paginate_queryset(orders)  # Применяем пагинацию
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

        # Функция для изменения статуса заказов

    def change_status_for_orders(self, status_new):
        one_hour_ago = timezone.now() - timedelta(hours=1)

        # Выбираем все заказы, где прошло больше 1 часа и статус не 'completed'
        orders = self.queryset.filter(
            Q(order_date__lt=one_hour_ago) & ~Q(status="completed")
        )

        # Изменяем статус для выбранных заказов
        orders.update(status=status_new)
        return orders

    @swagger_auto_schema(
        operation_summary="Изменить статус для заказов старше 1 часа",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый статус для заказов ('delivered')",
                )
            },
        ),
        responses={
            200: OrderSerializer(many=True),
            400: openapi.Response("Ошибка валидации данных"),
        },
    )
    @action(methods=["POST"], detail=False, url_path="change-status")
    def change_status(self, request):
        """
        Меняет статус заказов старше 1 часа на новый.
        """
        status_new = request.data.get("status")
        if not status_new:
            return Response(
                {"error": "Параметр 'status' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        # Проверка, что статус валиден
        valid_statuses = ["delivered", "cancelled", "preparing", "new"]
        if status_new not in valid_statuses:
            return Response(
                {"error": "Неверный статус."}, status=status_code.HTTP_400_BAD_REQUEST
            )

        # Меняем статус заказов
        orders = self.change_status_for_orders(status_new)

        # Сериализуем измененные заказы
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class OrderMenuItemViewSet(viewsets.ModelViewSet):
    queryset = OrderMenuItem.objects.all()
    serializer_class = OrderMenuItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["order__id", "menu_item__name"]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(operation_summary="Получить список позиций в заказах")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Получить позиции по заказу",
        manual_parameters=[
            openapi.Parameter(
                "order_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="ID заказа",
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="by-order")
    def items_by_order(self, request):
        """
        Возвращает позиции, связанные с определённым заказом.
        """
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response(
                {"error": "Параметр 'order_id' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        items = self.queryset.filter(order__id=order_id)
        page = self.paginate_queryset(items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
