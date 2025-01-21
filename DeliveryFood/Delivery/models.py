from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q, Manager
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    ROLES = [
        ("client", "Клиент"),
        ("courier", "Курьер"),
        ("admin", "Администратор"),
        ("restaurant_service", "Сервис ресторана"),
    ]
    history = HistoricalRecords()
    phone = models.CharField(max_length=18, verbose_name="Номер телефона")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес пользователя")
    role = models.CharField(
        max_length=20, choices=ROLES, verbose_name="Роль пользователя"
    )

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="delivery_user_set",
        blank=True,
        verbose_name="Группы пользователя",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="delivery_user_permissions_set",
        blank=True,
        verbose_name="Права пользователя",
    )

    # Пример clean_<fieldname>()
    def clean_phone(self):
        """Проверка корректности телефонного номера."""
        if not self.phone.startswith("+"):
            raise ValidationError("Номер телефона должен начинаться с '+'.")
        return self.phone

    # Пример save с commit=True
    def save(self, commit=True, *args, **kwargs):
        """
        Переопределённый метод save с поддержкой commit.
        Если commit=False, объект будет подготовлен, но не сохранён в базе данных.
        """
        if self.phone:
            self.phone = self.phone.replace("-", "").replace(" ", "")

        # Если commit=False, возвращаем объект без сохранения
        if not commit:
            return super(User, self).save_base(raw=False, *args, **kwargs)

        # Если commit=True, вызываем стандартный save
        super().save(*args, **kwargs)

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
    address = models.TextField(verbose_name="Адрес")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    description = models.TextField(null=True, blank=True, verbose_name="Описание ресторана")
    logo = models.ImageField(
        upload_to='restaurant_logos/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        verbose_name="Логотип ресторана"
    )
    cuisine_types = models.ManyToManyField(
        'TypeCuisine',
        related_name='restaurants',
        verbose_name="Типы кухни"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def get_cuisines(self):
        return ", ".join([cuisine.name for cuisine in self.cuisine_types.all()])
    get_cuisines.short_description = "Типы кухни"

    class Meta:
        verbose_name = "Ресторан"
        verbose_name_plural = "Рестораны"

    def __str__(self):
        return self.name


class MenuCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="Ресторан"
    )

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

    class Meta:
        verbose_name = "Категория меню"
        verbose_name_plural = "Категории меню"
        unique_together = ('name', 'restaurant')


class MenuItem(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey('MenuCategory', on_delete=models.SET_NULL, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)  # Для мягкого удаления
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

    def soft_delete(self):
        """Мягкое удаление"""
        self.is_active = False
        self.is_available = False
        self.save()



class Order(models.Model):
    history = HistoricalRecords()
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('delivering', 'Доставляется'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Ресторан",
    )
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Общая стоимость"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус заказа",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def update_total_price(self):
        """Обновляет общую стоимость заказа на основе позиций."""
        total = sum(item.get_total() for item in self.items.all())
        self.total_price = total
        self.save()

    def save(self, *args, **kwargs):
        """Переопределяем метод save для автоматического обновления общей стоимости."""
        is_new = self.pk is None  # Проверяем, новый ли объект
        super().save(*args, **kwargs)  # Сначала сохраняем объект
        if not is_new:  # Обновляем общую стоимость только для существующих объектов
            self.update_total_price()
            super().save(*args, **kwargs)  # Сохраняем снова после обновления цены

    def __str__(self):
        return f"Заказ {self.id} от {self.user.get_full_name()} из ресторана {self.restaurant.name}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderMenuItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name="Блюдо"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена на момент заказа"
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity} в заказе №{self.order.id}"

    def get_total(self):
        return self.price * self.quantity

class CourierManager(Manager):
    def by_vehicle_type(self, vehicle_type):
        return self.filter(vehicle_type=vehicle_type)

    def filtered(self, vehicle_types, first_name_starts_with, exclude_last_name_contains):
        query = Q()
        if vehicle_types:
            query &= Q(vehicle_type__in=vehicle_types.split(','))
        if first_name_starts_with:
            query &= Q(user__first_name__startswith=first_name_starts_with)
        if exclude_last_name_contains:
            query &= ~Q(user__last_name__icontains=exclude_last_name_contains)
        return self.filter(query)


class Courier(models.Model):
    history = HistoricalRecords()
    VEHICLE_CHOICES = [
        ("bike", "Велосипед"),
        ("car", "Машина"),
        ("scooter", "Скутер"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="courier_profile",
        verbose_name="Пользователь",
    )
    vehicle_type = models.CharField(
        max_length=20, choices=VEHICLE_CHOICES, verbose_name="Тип транспорта"
    )

    def __str__(self):
        return f"Курьер {self.user.get_full_name()}"

    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"

    objects = CourierManager()


class Delivery(models.Model):
    history = HistoricalRecords()
    STATUS_CHOICES = [
        ("in_progress", "В процессе"),
        ("delivered", "Доставлено"),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery", verbose_name="Заказ"
    )
    courier = models.ForeignKey(
        Courier,
        on_delete=models.CASCADE,
        related_name="deliveries",
        verbose_name="Курьер",
    )
    delivery_time = models.DateTimeField(
        blank=True, null=True, verbose_name="Время доставки"
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="in_progress",
        verbose_name="Статус доставки",
    )

    def get_absolute_url(self):
        """Возвращает абсолютный URL для просмотра деталей доставки."""
        return reverse("delivery_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"Доставка для заказа {self.order.id}"

    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"
