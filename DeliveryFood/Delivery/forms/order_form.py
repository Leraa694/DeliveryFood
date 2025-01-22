from django import forms
from ..models import Order, User


class OrderForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "data-live-search": "true",
        }),
        label="Пользователь",
    )
    additional_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Введите дополнительные примечания",
            "rows": 3,
        }),
        required=False,
        label="Дополнительные примечания",
    )

    class Meta:
        model = Order
        fields = ["user", "restaurant", "status", "additional_notes"]
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

    class Media:
        """
        Определяем CSS и JS файлы, которые нужны для работы формы.
        """
        css = {
            'all': ('Delivery/order/css/order_form.css',)  # Стили для формы
        }
        js = ('Delivery/order/js/order_form.js',)  # Скрипты для динамической обработки формы

