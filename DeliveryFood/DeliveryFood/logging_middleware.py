import logging
import json
from datetime import datetime
from django_redis import get_redis_connection

from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger('user_activity')


class LoggingMiddleware:
    def __init__(self, get_response):
        """
        Конструктор класса, который инициализирует необходимые объекты.
        """
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()
        self.redis_client = get_redis_connection("default") # Настройка Redis

    def __call__(self, request):
        """
        Метод, который обрабатывает каждый входящий HTTP-запрос.
        """
        user_info = "Анонимус"  # Значение по умолчанию для анонимных пользователей

        # Проверка на наличие авторизованного пользователя через стандартный механизм Django
        if request.user.is_authenticated:
            user_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
        else:
            try:
                token = request.headers.get('Authorization', '').split()[1]
                validated_token = self.jwt_authenticator.get_validated_token(token)
                user = self.jwt_authenticator.get_user(validated_token)
                user_info = f"{user.first_name} {user.last_name} ({user})"
            except Exception:
                pass

        visit_data = {
            "user": user_info,  # Информация о пользователе
            "path": request.path,  # URL, по которому был отправлен запрос
            "method": request.method,  # HTTP-метод (GET, POST и т.д.)
            "timestamp": datetime.now().isoformat(),  # Время запроса в формате ISO
        }

        # Запись данных в Redis
        self.redis_client.lpush("user_activity", json.dumps(visit_data))
        logger.info(f"Записано в Redis: {visit_data}")

        response = self.get_response(request)
        return response
