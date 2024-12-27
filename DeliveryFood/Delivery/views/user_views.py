from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import User
from ..serializers.user_serializers import UserSerializer
from django.db.models import Q


class UserViewSet(viewsets.ViewSet):
    """
    ViewSet для работы с пользователями.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    @swagger_auto_schema(
        operation_summary="Получить данные текущего пользователя",
        responses={200: UserSerializer()},
    )
    @action(methods=["GET"], detail=False, url_path="info")
    def user(self, request):
        """
        Возвращает данные текущего пользователя.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Обновить данные текущего пользователя",
        request_body=UserSerializer,
        responses={200: UserSerializer()},
    )
    @action(methods=["PUT"], detail=False, url_path="update")
    def update_user(self, request):
        """
        Обновляет данные текущего пользователя.
        """
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Получить список курьеров",
        responses={
            200: openapi.Response(
                description="Список курьеров",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                ),
            )
        },
    )
    @action(methods=["GET"], detail=False, url_path="couriers")
    def couriers(self, request):
        """
        Возвращает список пользователей с ролью 'courier'.
        """
        couriers = self.queryset.filter(role="courier")
        serializer = UserSerializer(couriers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Удалить пользователя",
        responses={
            204: openapi.Response(description="Пользователь успешно удален"),
            404: openapi.Response(description="Пользователь не найден"),
        },
    )
    @action(methods=["DELETE"], detail=True, url_path="delete")
    def delete_user(self, request, pk=None):
        """
        Удаляет пользователя с указанным id.
        """
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response(
                {"message": "Пользователь успешно удален."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_summary="Получить список клиентов",
        responses={200: UserSerializer(many=True)},
    )
    @action(methods=["GET"], detail=False, url_path="clients")
    def clients(self, request):
        """
        Возвращает список пользователей с ролью 'client'.
        """
        clients = self.queryset.filter(role="client")
        serializer = UserSerializer(clients, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Поиск пользователей по имени и фамилии",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Часть имени или фамилии",
            )
        ],
        responses={200: UserSerializer(many=True)},
    )
    @action(methods=["GET"], detail=False, url_path="search")
    def search_users(self, request):
        """
        Выполняет поиск пользователей по имени и фамилии.
        """
        search = request.query_params.get("search", "")
        if search:
            users = self.queryset.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "Параметр 'search' обязателен."},
            status=status.HTTP_400_BAD_REQUEST,
        )
