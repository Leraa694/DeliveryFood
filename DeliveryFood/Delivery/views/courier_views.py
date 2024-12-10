from datetime import timedelta

from pkg_resources import require
from rest_framework import viewsets, permissions, filters, status as status_code
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import action
from ..models import Courier, Delivery
from ..serializers.courier_serializers import CourierSerializer, DeliverySerializer

class StandardResultsSetPagination(PageNumberPagination):
    """
    Кастомная пагинация для стандартного набора результатов.
    """
    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр для задания размера страницы через запрос
    max_page_size = 100  # Максимальное количество элементов на странице

class CourierViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    @swagger_auto_schema(operation_summary="Получить список курьеров")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Создать нового курьера")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Обновить данные курьера")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить курьеров по типу транспорта",
        manual_parameters=[
            openapi.Parameter('vehicle_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Тип транспорта курьера'),
        ],
    )
    @action(methods=['GET'], detail=False, url_path='by-vehicle-type')
    def couriers_by_vehicle_type(self, request):
        """
        Возвращает курьеров, у которых указан определённый тип транспорта.
        """
        vehicle_type = request.query_params.get('vehicle_type')
        if not vehicle_type:
            return Response({"error": "Параметр 'vehicle_type' обязателен."}, status=status_code.HTTP_400_BAD_REQUEST)

        couriers = self.queryset.filter(vehicle_type=vehicle_type)
        page = self.paginate_queryset(couriers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(couriers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Фильтрация курьеров по условиям",
        manual_parameters=[
            openapi.Parameter(
                'vehicle_type',
                openapi.IN_QUERY,
                description="Типы транспорта через запятую (например, 'bike,car')",
                type=openapi.TYPE_STRING,
                require=True
            ),
            openapi.Parameter(
                'first_name_starts_with',
                openapi.IN_QUERY,
                description="Имя пользователя, начинающееся с указанной буквы",
                type=openapi.TYPE_STRING,
                require=True
            ),
            openapi.Parameter(
                'exclude_last_name_contains',
                openapi.IN_QUERY,
                description="Исключить пользователей с фамилией, содержащей указанное значение",
                type=openapi.TYPE_STRING,
                require=True
            )
        ],
        responses={
            200: CourierSerializer(many=True),
            400: openapi.Response("Ошибка валидации параметров")
        }
    )
    @action(methods=['GET'], detail=False, url_path='filtered-couriers')
    def filtered_couriers(self, request):
        """
        Фильтрация курьеров на основе нескольких критериев.
        """
        vehicle_types = request.query_params.get('vehicle_type')
        first_name_starts_with = request.query_params.get('first_name_starts_with')
        exclude_last_name_contains = request.query_params.get('exclude_last_name_contains')

        # Базовый фильтр без условий
        vehicle_filter = Q()

        # Добавляем фильтр по типу транспорта
        if vehicle_types:
            vehicle_type_filters = Q()
            for vehicle_type in vehicle_types.split(","):
                vehicle_type_filters |= Q(vehicle_type=vehicle_type)
            vehicle_filter &= vehicle_type_filters

        # Добавляем фильтр по начальной букве имени
        if first_name_starts_with:
            vehicle_filter &= Q(user__first_name__startswith=first_name_starts_with)

        # Исключаем по подстроке в фамилии
        if exclude_last_name_contains:
            vehicle_filter &= ~Q(user__last_name__icontains=exclude_last_name_contains)

        # Применяем фильтры к queryset
        couriers = self.queryset.filter(vehicle_filter)

        # Проверяем, что возвращается корректный результат
        page = self.paginate_queryset(couriers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(couriers, many=True)
        return Response(serializer.data, status=status_code.HTTP_200_OK)

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['order__id', 'courier__user__username']
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(operation_summary="Получить список доставок")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Создать новую доставку")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Обновить данные доставки")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить доставки по статусу",
        manual_parameters=[
            openapi.Parameter('delivery_status', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Статус доставки'),
        ],
    )
    @action(methods=['GET'], detail=False, url_path='by-status')
    def deliveries_by_status(self, request):
        """
        Возвращает доставки с указанным статусом.
        """
        delivery_status = request.query_params.get('delivery_status')
        if not delivery_status:
            return Response({"error": "Параметр 'delivery_status' обязателен."}, status=status_code.HTTP_400_BAD_REQUEST)

        deliveries = self.queryset.filter(delivery_status=delivery_status)
        page = self.paginate_queryset(deliveries)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deliveries, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Изменить статус доставки",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'delivery_status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый статус доставки ('in_progress', 'delivered')"
                )
            },
        ),
        responses={200: DeliverySerializer(many=True), 400: openapi.Response("Ошибка валидации данных")},
    )
    @action(methods=['POST'], detail=False, url_path='change-status')
    def change_delivery_status(self, request):
        """
        Меняет статус доставок на новый.
        """
        delivery_status = request.data.get('delivery_status')
        if not delivery_status:
            return Response({"error": "Параметр 'delivery_status' обязателен."}, status=status_code.HTTP_400_BAD_REQUEST)

        valid_statuses = ['in_progress', 'delivered']
        if delivery_status not in valid_statuses:
            return Response({"error": "Неверный статус доставки."}, status=status_code.HTTP_400_BAD_REQUEST)

        deliveries = self.queryset.filter(~Q(delivery_status='delivered'))
        deliveries.update(delivery_status=delivery_status)

        serializer = self.get_serializer(deliveries, many=True)
        return Response(serializer.data)


