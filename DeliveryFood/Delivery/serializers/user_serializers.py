from rest_framework import serializers
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from ..models import User

class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Номер телефона должен быть в формате '+999999999'. До 15 цифр."
            )
        ],
        required=True
    )

    def validate_role(self, value):
        if value not in ['client', 'courier', 'admin']:
            raise serializers.ValidationError("Недопустимая роль пользователя.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.password = make_password(password)
        user.save()
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name', 'phone', 'address', 'role')
        extra_kwargs = {'password': {'write_only': True}}
