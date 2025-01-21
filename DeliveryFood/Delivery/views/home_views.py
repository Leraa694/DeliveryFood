from django.shortcuts import render
from django.db.models import Count, Avg
from ..models import Restaurant, MenuItem, TypeCuisine, Order

def home(request):
    # Получаем все типы кухонь
    cuisines = TypeCuisine.objects.all()
    
    # Получаем топ ресторанов
    top_restaurants = Restaurant.objects.annotate(
        menu_items_count=Count('menu_items'),
        orders_count=Count('orders')
    ).filter(
        menu_items__is_available=True
    ).order_by('-orders_count', '-menu_items_count')[:6]
    
    # Получаем популярные блюда
    sort_param = request.GET.get('sort', 'orders')
    if sort_param == 'price':
        popular_dishes = MenuItem.objects.order_by('price')
    else:  # sort by orders count
        popular_dishes = MenuItem.objects.annotate(
            orders_count=Count('order_items')
        ).order_by('-orders_count')
    
    popular_dishes = popular_dishes.filter(is_available=True)[:8]
    
    # Получаем текущий заказ пользователя
    current_order = None
    if request.user.is_authenticated:
        current_order = Order.objects.filter(
            user=request.user,
            status__in=['new', 'preparing', 'delivering']
        ).first()
    
    context = {
        'cuisines': cuisines,
        'top_restaurants': top_restaurants,
        'popular_dishes': popular_dishes,
        'current_order': current_order,
    }
    
    return render(request, 'home.html', context)

def search(request):
    query = request.GET.get('q', '')
    
    # Поиск ресторанов
    restaurants = Restaurant.objects.filter(name__icontains=query)
    
    # Поиск блюд
    menu_items = MenuItem.objects.filter(
        name__icontains=query,
        is_available=True
    )
    
    # Поиск по типам кухни
    cuisines = TypeCuisine.objects.filter(name__icontains=query)
    
    context = {
        'query': query,
        'restaurants': restaurants,
        'menu_items': menu_items,
        'cuisines': cuisines,
    }
    
    return render(request, 'search_results.html', context)
