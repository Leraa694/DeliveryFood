from django import forms
from ..models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["user", "restaurant", "status", "order_date"]
        widgets = {
            "user": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите имя пользователя",
                "maxlength": 50,
            }),
            "restaurant": forms.Select(attrs={
                "class": "form-select",
                "data-live-search": "true",  # Пример атрибута для работы с JS-библиотеками
            }),
            "status": forms.RadioSelect(attrs={
                "class": "form-check-input",
            }),
            "order_date": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control",
            }),
        }
        labels = {
            "user": "Пользователь",
            "restaurant": "Ресторан",
            "status": "Статус заказа",
            "order_date": "Дата и время заказа",
        }
        help_texts = {
            "user": "Укажите имя пользователя, который сделал заказ.",
            "restaurant": "Выберите ресторан, в котором был сделан заказ.",
            "status": "Выберите текущий статус заказа.",
            "order_date": "Укажите дату и время оформления заказа.",
        }
        error_messages = {
            "user": {
                "required": "Поле 'Пользователь' обязательно для заполнения.",
                "max_length": "Имя пользователя не должно превышать 50 символов.",
            },
            "restaurant": {
                "required": "Необходимо выбрать ресторан.",
            },
            "status": {
                "required": "Пожалуйста, выберите статус заказа.",
            },
            "order_date": {
                "invalid": "Введите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ.",
            },
        }
