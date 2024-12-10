from rest_framework import serializers
from ..models import Order, OrderMenuItem


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    # Валидация на общую стоимость
    def validate_total_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Общая стоимость не может быть отрицательной.")
        return value

    # Валидация на статус
    def validate_status(self, value):
        valid_statuses = ['new', 'preparing', 'delivering', 'completed']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Статус заказа должен быть одним из: {', '.join(valid_statuses)}.")
        return value

    # Дополнительная валидация
    def validate(self, data):
        # Если статус "completed", проверим, что заказ имеет допустимую цену
        if data.get('status') == 'completed' and data.get('total_price', 0) <= 0:
            raise serializers.ValidationError("Для статуса 'completed' общая стоимость должна быть положительной.")
        return data

    def create(self, validated_data):
        # Создаём заказ без деталей
        order = Order.objects.create(**validated_data)
        return order

    def update(self, instance, validated_data):
        # Обновляем основные данные заказа
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class OrderMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderMenuItem
        fields = '__all__'

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть больше нуля.")
        return value

    def validate(self, data):
        if data['menu_item'].restaurant != data['order'].restaurant:
            raise serializers.ValidationError("Ресторан блюда должен совпадать с рестораном заказа.")
        return data
