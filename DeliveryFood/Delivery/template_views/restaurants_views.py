from django.shortcuts import render, get_object_or_404, redirect
from ..models import Order, Restaurant
from ..forms.order_form import OrderForm

def restaurant_list(request):
    query = request.GET.get("search", "")  # Get the search query from the request
    queryset = Restaurant.objects.all()

    # Фильтрация по названию заявки
    if query:
        queryset = queryset.filter(name__icontains=query)

    restaurants = Restaurant.objects.filter(name__icontains=query)  # Filter restaurants by name
    return render(request, "Delivery/restaurant/restaurant.html", {"restaurants": restaurants, "search": query})