from django import forms
from ..models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["user", "restaurant", "status"]  # Удаляем 'order_date'
        widgets = {
            "user": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите имя пользователя",
            }),
            "restaurant": forms.Select(attrs={
                "class": "form-select",
                "data-live-search": "true",
            }),
            "status": forms.RadioSelect(attrs={
                "class": "form-check-input",
            }),
        }
        labels = {
            "user": "Пользователь",
            "restaurant": "Ресторан",
            "status": "Статус заказа",
        }
        help_texts = {
            "user": "Укажите имя пользователя, который сделал заказ.",
            "restaurant": "Выберите ресторан, в котором был сделан заказ.",
            "status": "Выберите текущий статус заказа.",
        }
        error_messages = {
            "user": {
                "required": "Поле 'Пользователь' обязательно для заполнения.",
            },
            "restaurant": {
                "required": "Необходимо выбрать ресторан.",
            },
            "status": {
                "required": "Пожалуйста, выберите статус заказа.",
            },
        }
