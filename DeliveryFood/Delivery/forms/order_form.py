from django import forms
from ..models import Order, User, Restaurant


class OrderForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "data-live-search": "true"}),
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
    image = forms.ImageField(
        required=False,
        label="Изображение к заказу",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    link_dogovor = forms.URLField(
        required=False,
        label="Ссылка на договор",
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Order
        fields = ["user", "restaurant", "status", "additional_notes", "link_dogovor", "image"]
        widgets = {
            "restaurant": forms.Select(attrs={"class": "form-select", "data-live-search": "true"}),
            "status": forms.RadioSelect(attrs={"class": "form-check-input"}),
        }
        labels = {
            "user": "Пользователь",
            "restaurant": "Ресторан",
            "status": "Статус заказа",
        }
        help_texts = {
            "user": "Укажите пользователя, который оформляет заказ.",
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
        css = {
            'all': ('Delivery/order/css/order_form.css',)
        }
        js = ('Delivery/order/js/order_form.js',)

from django.forms import inlineformset_factory
from ..models import Order, OrderMenuItem

OrderItemFormSet = inlineformset_factory(
    Order,
    OrderMenuItem,
    fields=["menu_item", "quantity"],
    extra=5,              # Количество «пустых» форм по умолчанию
    can_delete=True       # Разрешить удалять позиции
)
