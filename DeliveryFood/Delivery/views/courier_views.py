from rest_framework import viewsets, permissions, filters, status as status_code
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db.models import Q, Manager
from rest_framework.decorators import action
from ..models import Courier, Delivery
from ..serializers.courier_serializers import CourierSerializer, DeliverySerializer


class StandardResultsSetPagination(PageNumberPagination):
    """
    Кастомная пагинация для стандартного набора результатов.
    """

    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = (
        "page_size"  # Параметр для задания размера страницы через запрос
    )
    max_page_size = 100  # Максимальное количество элементов на странице


class CourierViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username", "user__first_name", "user__last_name"]

    @swagger_auto_schema(operation_summary="Получить список курьеров")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить курьеров по типу транспорта",
        manual_parameters=[
            openapi.Parameter(
                "vehicle_type",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Тип транспорта курьера",
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="by-vehicle-type")
    def couriers_by_vehicle_type(self, request):
        vehicle_type = request.query_params.get("vehicle_type")
        if not vehicle_type:
            return Response({"error": "Параметр 'vehicle_type' обязателен."},
                            status=status_code.HTTP_400_BAD_REQUEST)

        couriers = Courier.objects.by_vehicle_type(vehicle_type)
        return self.get_paginated_response_or_list(couriers)

    @swagger_auto_schema(
        operation_summary="Фильтрация курьеров по условиям",
        manual_parameters=[
            openapi.Parameter(
                "vehicle_type",
                openapi.IN_QUERY,
                description="Типы транспорта через запятую",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "first_name_starts_with",
                openapi.IN_QUERY,
                description="Имя, начинающееся с определенной буквы",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "exclude_last_name_contains",
                openapi.IN_QUERY,
                description="Исключить фамилии, содержащие определенную подстроку",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: CourierSerializer(many=True),
            400: openapi.Response("Ошибка валидации параметров"),
        },
    )
    @action(methods=["GET"], detail=False, url_path="filtered-couriers")
    def filtered_couriers(self, request):
        vehicle_types = request.query_params.get("vehicle_type")
        first_name_starts_with = request.query_params.get("first_name_starts_with")
        exclude_last_name_contains = request.query_params.get("exclude_last_name_contains")

        couriers = Courier.objects.filtered(
            vehicle_types, first_name_starts_with, exclude_last_name_contains
        )
        return self.get_paginated_response_or_list(couriers)

    def get_paginated_response_or_list(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Получить количество активных курьеров",
        responses={
            200: openapi.Response(
                description="Количество активных курьеров",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "active_couriers_count": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Количество активных курьеров",
                        )
                    },
                ),
            )
        },
    )
    @action(methods=["GET"], detail=False, url_path="active-couriers-stats")
    def get_active_couriers_stats(self, request):
        """
        Возвращает статистику активных курьеров по типу транспорта.
        """
        vehicle_stats = {
            vehicle: Courier.objects.filter(vehicle_type=vehicle, user__is_active=True).count()
            for vehicle, _ in Courier.VEHICLE_CHOICES
        }
        total_active = sum(vehicle_stats.values())
        vehicle_stats["total_active"] = total_active
        return Response(vehicle_stats, status=status_code.HTTP_200_OK)


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["order__id", "courier__user__username"]
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
            openapi.Parameter(
                "delivery_status",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Статус доставки",
            ),
        ],
    )
    @action(methods=["GET"], detail=False, url_path="by-status")
    def deliveries_by_status(self, request):
        """
        Возвращает доставки с указанным статусом.
        """
        delivery_status = request.query_params.get("delivery_status")
        if not delivery_status:
            return Response(
                {"error": "Параметр 'delivery_status' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

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
                "delivery_status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый статус доставки ('in_progress', 'delivered')",
                )
            },
        ),
        responses={
            200: DeliverySerializer(many=True),
            400: openapi.Response("Ошибка валидации данных"),
        },
    )
    @action(methods=["POST"], detail=False, url_path="change-status")
    def change_delivery_status(self, request):
        """
        Меняет статус доставок на новый.
        """
        delivery_status = request.data.get("delivery_status")
        if not delivery_status:
            return Response(
                {"error": "Параметр 'delivery_status' обязателен."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = ["in_progress", "delivered"]
        if delivery_status not in valid_statuses:
            return Response(
                {"error": "Неверный статус доставки."},
                status=status_code.HTTP_400_BAD_REQUEST,
            )

        deliveries_query = self.queryset.filter(~Q(delivery_status="delivered"))

        # Проверка наличия записей перед обновлением
        if not deliveries_query.exists():
            return Response({"error": "Нет доставок для изменения."}, status=status_code.HTTP_404_NOT_FOUND)

        deliveries_query.update(delivery_status=delivery_status)

        serializer = self.get_serializer(deliveries_query, many=True)
        return Response(serializer.data)
