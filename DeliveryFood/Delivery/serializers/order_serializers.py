from rest_framework import serializers
from ..models import Order, OrderDetail

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = '__all__'

    # Валидация на количество
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество не может быть меньше или равно нулю.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailSerializer(many=True, read_only=True)

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

    # Дополнительная валидация, если требуется
    def validate(self, data):
        # Например, если статус "completed", то проверим, что есть детали заказа
        if data['status'] == 'completed' and not data['order_details']:
            raise serializers.ValidationError("Для статуса 'completed' должны быть добавлены детали заказа.")
        return data