from rest_framework import viewsets, permissions, filters, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from rest_framework.decorators import action
from ..models import Order
from ..serializers.order_serializers import OrderSerializer
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter, NumberFilter
from rest_framework.pagination import PageNumberPagination


# Кастомный класс фильтрации (если нужен)
class OrderFilter(FilterSet):
    restaurant_name = CharFilter(field_name='restaurant__name', lookup_expr='icontains')
    min_price = NumberFilter(field_name='total_price', lookup_expr='gte')
    max_price = NumberFilter(field_name='total_price', lookup_expr='lte')

    class Meta:
        model = Order
        fields = ['restaurant_name', 'min_price', 'max_price']


class StandardResultsSetPagination(PageNumberPagination):
    """
    Кастомная пагинация для стандартного набора результатов.
    """
    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр для задания размера страницы через запрос
    max_page_size = 100  # Максимальное количество элементов на странице


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с заказами.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter  # Подключаем кастомный фильтр
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        operation_summary="Получить список заказов с фильтрацией и пагинацией",
        manual_parameters=[
            openapi.Parameter(
                'restaurant_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Название ресторана'
            ),
            openapi.Parameter(
                'min_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description='Минимальная цена заказа'
            ),
            openapi.Parameter(
                'max_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description='Максимальная цена заказа'
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Номер страницы'
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Размер страницы'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Возвращает список заказов с фильтрацией и пагинацией.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)  # Применяем пагинацию
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)  # Возвращаем пагинированный ответ

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    @swagger_auto_schema(
        operation_summary="Получить информацию о заказе по ID",
        responses={
            200: OrderSerializer(),
            404: openapi.Response("Заказ не найден"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Возвращает информацию о конкретном заказе по ID.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новый заказ",
        request_body=OrderSerializer,
        responses={
            201: OrderSerializer(),
            400: openapi.Response("Ошибка валидации данных"),
        },
    )
    def create(self, request, *args, **kwargs):
        """
        Создает новый заказ.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить заказ по ID",
        responses={
            204: openapi.Response("Заказ успешно удален"),
            404: openapi.Response("Заказ не найден"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """
        Удаляет заказ по ID.
        """
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить статус заказа",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый статус заказа ('new', 'preparing', 'delivering', 'completed')"
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
                'user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='ID пользователя'
            ),
        ],
        responses={200: OrderSerializer(many=True)},
    )
    @action(methods=['GET'], detail=False, url_path='by-user')
    def orders_by_user(self, request):
        """
        Возвращает заказы, сделанные определенным пользователем.
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "Параметр 'user_id' обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        orders = self.queryset.filter(user__id=user_id)
        page = self.paginate_queryset(orders)  # Применяем пагинацию
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)