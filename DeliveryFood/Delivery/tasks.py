from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from .models import Delivery, Order
import json
from django.utils.dateparse import parse_datetime
from celery import shared_task
from .models import UserActivity
from django_redis import get_redis_connection



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

@shared_task
def mark_overdue_orders():
    """
    Задача Celery для автоматической установки статуса "Отменен" у заказов,
    которые не были завершены в течение 3 часов.
    """
    # Определяем временную границу (3 часа назад)
    overdue_threshold = now() - timedelta(hours=3)

    # Выбираем заказы, которые не завершены и старше 3 часов
    overdue_orders = Order.objects.filter(
        status__in=["new", "preparing", "delivering"],  # Не завершенные статусы
        order_date__lt=overdue_threshold,  # Заказы старше 3 часов
    )

    # Обновляем статус каждого просроченного заказа
    for order in overdue_orders:
        order.status = "cancelled"
        order.save()

@shared_task
def save_user_activity_to_db():
    """
    Задача для сохранения активности пользователя из Redis в базу данных.
    """
    # Подключаемся к Redis через django-redis
    redis_client = get_redis_connection("default")
    activities = []

    while True:
        # Получаем данные активности пользователя из Redis
        visit_data = redis_client.rpop("user_activity")
        if not visit_data:
            break
        visit = json.loads(visit_data)

        # Добавляем данные в список для пакетного сохранения
        activities.append(UserActivity(
            user=visit["user"],  # Используем user_id для оптимизации
            path=visit["path"],
            method=visit["method"],
            timestamp=parse_datetime(visit["timestamp"]),
        ))

    # Сохраняем данные в базу данных одним запросом
    if activities:
        UserActivity.objects.bulk_create(activities)