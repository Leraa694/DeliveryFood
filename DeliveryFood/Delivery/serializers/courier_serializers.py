from rest_framework import serializers
from ..models import Courier, Delivery


class CourierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = "__all__"

    # Валидация для типа транспорта курьера
    def validate_vehicle_type(self, value):
        allowed_types = [choice[0] for choice in Courier.VEHICLE_CHOICES]
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Тип транспорта должен быть одним из: {', '.join(allowed_types)}."
            )
        return value


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"

    # Валидация для статуса доставки
    def validate_delivery_status(self, value):
        allowed_statuses = [choice[0] for choice in Delivery.STATUS_CHOICES]
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Статус доставки должен быть одним из: {', '.join(allowed_statuses)}."
            )
        return value
