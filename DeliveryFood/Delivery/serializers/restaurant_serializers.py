from rest_framework import serializers
from ..models import Restaurant, MenuItem


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"

    # Валидация для названия ресторана
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Название ресторана не может быть пустым."
            )
        return value

    # Валидация для номера телефона ресторана
    def validate_phone(self, value):
        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError(
                "Номер телефона должен содержать от 10 до 15 символов."
            )
        return value


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"

    # Валидация для названия блюда
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Название блюда не может быть пустым.")
        return value

    # Валидация для цены
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена блюда должна быть больше нуля.")
        return value

    # Валидация для статуса доступности блюда
    def validate_is_available(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError(
                "Поле 'Доступно ли блюдо' должно быть булевым значением."
            )
        return value
