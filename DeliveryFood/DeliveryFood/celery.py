from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем настройки Django по умолчанию для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DeliveryFood.settings')

app = Celery('DeliveryFood')

# Загружаем настройки из Django settings с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи из приложений
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {
    'send_delivery_notification': {
        'task': 'Delivery.tasks.send_delivery_notification',
        'schedule': crontab(minute='*'),  # Каждую минуту
    },
    'mark_overdue_orders': {
        'task': 'Delivery.tasks.mark_overdue_orders',
        'schedule': crontab(minute='*/15'),  # Каждые 15 минут
    },
    'save_user_activity_to_db': {
        'task': 'Delivery.tasks.save_user_activity_to_db',
        'schedule': crontab(minute='*'),
    },
}
