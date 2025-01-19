from django import forms
from ..models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["user", "restaurant", "status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }