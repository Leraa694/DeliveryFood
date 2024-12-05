from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from ..serializers.user_serializers import UserSerializer

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet для регистрации и управления токенами.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        request_body=UserSerializer,
        responses={
            201: openapi.Response("Пользователь успешно зарегистрирован", UserSerializer),
            400: openapi.Response("Ошибка валидации"),
        },
    )
    @action(methods=['POST'], detail=False, url_path='register')
    def register(self, request):
        """
        Регистрация нового пользователя.
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Пользователь успешно зарегистрирован", "user": UserSerializer(user).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Выход (аннулирование токенов)",
        responses={200: openapi.Response("Токены успешно аннулированы")},
    )
    @action(methods=['POST'], detail=False, url_path='logout')
    def logout(self, request):
        """
        Выход пользователя. Аннулирует токены.
        """
        try:
            refresh_token = request.data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Требуется настройка Blacklist в SimpleJWT
            return Response({"message": "Вы успешно вышли из системы."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Некорректный токен или ошибка при аннулировании."}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Представление для получения пары токенов: access и refresh.
    """
    @swagger_auto_schema(
        operation_summary="Получить JWT токены (access и refresh)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Пароль"),
            },
        ),
        responses={
            200: openapi.Response(
                "Токены успешно выданы",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh токен"),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="Access токен"),
                    },
                ),
            ),
            401: openapi.Response("Неверные учетные данные"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Аутентификация и получение пары токенов.
        """
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Представление для обновления токена.
    """
    @swagger_auto_schema(
        operation_summary="Обновить токен",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh токен"),
            },
        ),
        responses={
            200: openapi.Response(
                "Access токен успешно обновлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="Access токен"),
                    },
                ),
            ),
            401: openapi.Response("Некорректный refresh токен"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Обновление токена.
        """
        return super().post(request, *args, **kwargs)
