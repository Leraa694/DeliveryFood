from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    ROLES = [
        ('client', 'Клиент'),
        ('courier', 'Курьер'),
        ('admin', 'Администратор'),
        ('restaurant_service', 'Сервис ресторана'),
    ]

    phone = models.CharField(max_length=18, verbose_name="Номер телефона")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес пользователя")
    role = models.CharField(max_length=20, choices=ROLES, verbose_name="Роль пользователя")

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='delivery_user_set',
        blank=True,
        verbose_name="Группы пользователя"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='delivery_user_permissions_set',
        blank=True,
        verbose_name="Права пользователя"
    )

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class TypeCuisine(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название типа кухни")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип кухни"
        verbose_name_plural = "Типы кухонь"


class Restaurant(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название ресторана")
    address = models.TextField(verbose_name="Адрес ресторана")
    phone = models.CharField(max_length=15, verbose_name="Телефон ресторана")
    cuisine_types = models.ManyToManyField(
        TypeCuisine,
        related_name='restaurants',
        verbose_name="Типы кухни"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ресторан"
        verbose_name_plural = "Рестораны"


class MenuItem(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название блюда")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(blank=True, null=True, verbose_name="Описание блюда")
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name="Ресторан"
    )
    is_available = models.BooleanField(default=True, verbose_name="Доступно ли блюдо")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"


class Order(models.Model):
    history = HistoricalRecords()
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('preparing', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('completed', 'Завершён'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Пользователь"
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Ресторан"
    )
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Общая стоимость"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус заказа"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def update_total_price(self):
        """Обновляет общую стоимость заказа на основе позиций."""
        self.total_price = sum(
            item.price for item in self.order_items.all()
        )

    def save(self, *args, **kwargs):
        """Переопределяем метод save для автоматического обновления общей стоимости."""
        is_new = self.pk is None  # Проверяем, новый ли объект
        super().save(*args, **kwargs)  # Сначала сохраняем объект
        if not is_new:  # Обновляем общую стоимость только для существующих объектов
            self.update_total_price()
            super().save(*args, **kwargs)  # Сохраняем снова после обновления цены

    def __str__(self):
        return f"Заказ {self.id} от {self.user.get_full_name()}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"



class OrderMenuItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Заказ"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Блюдо"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество", default=1)

    @property
    def price(self):
        """Вычисляет стоимость позиции на основе цены блюда."""
        return self.menu_item.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} для заказа {self.order.id}"

    class Meta:
        verbose_name = "Позиция в заказе"
        verbose_name_plural = "Позиции в заказе"


class Courier(models.Model):
    VEHICLE_CHOICES = [
        ('bike', 'Велосипед'),
        ('car', 'Машина'),
        ('scooter', 'Скутер'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='courier_profile',
        verbose_name="Пользователь"
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_CHOICES,
        verbose_name="Тип транспорта"
    )

    def __str__(self):
        return f"Курьер {self.user.get_full_name()}"

    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"


class Delivery(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'В процессе'),
        ('delivered', 'Доставлено'),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery',
        verbose_name="Заказ"
    )
    courier = models.ForeignKey(
        Courier,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name="Курьер"
    )
    delivery_time = models.DateTimeField(blank=True, null=True, verbose_name="Время доставки")
    delivery_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name="Статус доставки"
    )

    def __str__(self):
        return f"Доставка для заказа {self.order.id}"

    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"
