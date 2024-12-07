from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Delivery'  # Имя вашего приложения

    def ready(self):
        import Delivery.signals  # Укажите путь к вашему signals.py