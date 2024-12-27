from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from .models import Delivery

@shared_task
def send_delivery_notification():
    """
    Задача для отправки уведомлений пользователям за 5 минут до доставки.
    """
    # Получаем текущее время
    current_time = now()

    # Фильтруем доставки, которые должны быть выполнены через 5 минут
    target_time_start = current_time + timedelta(minutes=5)
    target_time_end = target_time_start + timedelta(minutes=1)

    upcoming_deliveries = Delivery.objects.filter(
        delivery_time__gte=target_time_start,  # Доставка начинается через 5 минут или позже
        delivery_time__lt=target_time_end,  # Доставка начинается в пределах минуты от целевого времени
        delivery_status="in_progress"  # Доставка еще не завершена
    )

    for delivery in upcoming_deliveries:
        order = delivery.order
        user_email = order.user.email
        courier_name = delivery.courier.user.get_full_name()
        vehicle_type = delivery.courier.get_vehicle_type_display()

        if user_email:
            send_mail(
                subject='Курьер уже в пути!',
                message=(
                    f'Здравствуйте, {order.user.get_full_name()}!\n\n'
                    f'Напоминаем, что доставка вашего заказа №{order.id} из ресторана '
                    f'"{order.restaurant.name}" будет выполнена в течение 5 минут.\n'
                    f'Курьер: {courier_name}, транспорт: {vehicle_type}.\n'
                    f'Пожалуйста, ожидайте!'
                ),
                from_email='admin@leradelivery.com',
                recipient_list=[user_email],
            )
