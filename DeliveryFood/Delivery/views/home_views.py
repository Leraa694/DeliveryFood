from django.db.models import Count
from django.shortcuts import render
from ..models import Restaurant, MenuItem, Order, TypeCuisine
from django.shortcuts import render, get_object_or_404


def home(request):
    # Простая статистика
    total_restaurants = Restaurant.objects.count()
    total_dishes = MenuItem.objects.count()
    total_orders = Order.objects.count()

    # Топ 5 ресторанов (по количеству заказов и количеству блюд)
    top_restaurants = (
        Restaurant.objects.annotate(
            menu_items_count=Count('menu_items'),
            orders_count=Count('orders')
        )
        .filter(menu_items__is_available=True)
        .order_by('-orders_count', '-menu_items_count')[:5]
    )

    # Топ 5 популярных блюд (по количеству "вхождений" в заказы)
    popular_dishes = (
        MenuItem.objects.filter(is_available=True)
        .annotate(orders_count=Count('order_items'))
        .order_by('-orders_count')[:5]
    )

    # Топ 5 текущих заказов (заявок): статусы new / preparing / delivering
    current_orders = (
        Order.objects.filter(status__in=['new', 'preparing', 'delivering'])
        .order_by('-created_at')[:5]
    )

    context = {
        'total_restaurants': total_restaurants,
        'total_dishes': total_dishes,
        'total_orders': total_orders,
        'top_restaurants': top_restaurants,
        'popular_dishes': popular_dishes,
        'current_orders': current_orders,
    }
    return render(request, 'Delivery/main/home.html', context)


def top_restaurants_list(request):
    query = request.GET.get('q', '')

    # Получаем список всех ресторанов (при желании — тех, у которых есть доступные блюда)
    restaurants = Restaurant.objects.annotate(
        menu_items_count=Count('menu_items'),
        orders_count=Count('orders')
    ).filter(menu_items__is_available=True)

    # Поиск по имени ресторана
    if query:
        restaurants = restaurants.filter(name__icontains=query)

    # Сортируем по количеству заказов и блюд
    restaurants = restaurants.order_by('-orders_count', '-menu_items_count')

    context = {
        'restaurants': restaurants,
        'query': query,
    }
    return render(request, 'Delivery/main/top_restaurants_list.html', context)


from django.db.models import Count
from django.shortcuts import render


def popular_dishes_list(request):
    query = request.GET.get('q', '')
    # Фильтруем доступные блюда
    menu_items = MenuItem.objects.filter(is_available=True).annotate(
        orders_count=Count('order_items')
    ).order_by('-orders_count')

    # Поиск по названию блюда
    if query:
        menu_items = menu_items.filter(name__icontains=query)

    context = {
        'menu_items': menu_items,
        'query': query,
    }
    return render(request, 'Delivery/main/popular_dishes_list.html', context)


from django.shortcuts import render


def current_orders_list(request):
    query = request.GET.get('q', '')
    # Текущие заказы: статусы new, preparing, delivering
    orders = Order.objects.filter(status__in=['new', 'preparing', 'delivering']).select_related('restaurant', 'user')

    # Простой поиск по названию ресторана (можно расширить)
    if query:
        orders = orders.filter(restaurant__name__icontains=query)

    orders = orders.order_by('-created_at')
    context = {
        'orders': orders,
        'query': query,
    }
    return render(request, 'Delivery/main/current_orders_list.html', context)




def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    # Типы кухни (через M2M)
    cuisines = restaurant.cuisine_types.all()
    # Доступные блюда ресторана
    menu_items = restaurant.menu_items.filter(is_available=True)

    context = {
        'restaurant': restaurant,
        'cuisines': cuisines,
        'menu_items': menu_items,
    }
    return render(request, 'Delivery/main/restaurant_detail.html', context)

def dish_detail(request, pk):
    dish = get_object_or_404(MenuItem, pk=pk)
    context = {
        'dish': dish,
    }
    return render(request, 'Delivery/main/dish_detail.html', context)

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_items = order.order_items.select_related('menu_item')
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'Delivery/main/order_detail.html', context)

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