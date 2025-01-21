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
    def save(self, *args, **kwargs):
        """Сохраняет объект с обработкой дополнительных полей."""
        # Дополнительная обработка перед сохранением
        if self.phone:
            self.phone = self.phone.replace("-", "").replace(" ", "")
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"


    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class RestaurantCuisine(models.Model):
    """Промежуточная модель для связи ресторанов с типами кухни."""
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.CASCADE,
        related_name='restaurant_cuisines',
        verbose_name="Ресторан"
    )
    cuisine_type = models.ForeignKey(
        'TypeCuisine',
        on_delete=models.CASCADE,
        related_name='restaurant_cuisines',
        verbose_name="Тип кухни"
    )
    popularity = models.PositiveIntegerField(
        default=0, verbose_name="Популярность блюда"
    )
    def __str__(self):
        return f"{self.restaurant.name} - {self.cuisine_type.name}"
    class Meta:
        verbose_name = "Связь ресторана и кухни"
        verbose_name_plural = "Связи ресторанов и кухонь"
        unique_together = ('restaurant', 'cuisine_type')

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
    phone = models.CharField(max_length=18, verbose_name="Телефон ресторана")
    cuisine_types = models.ManyToManyField(
        TypeCuisine, related_name="restaurants", verbose_name="Типы кухни",
        through='RestaurantCuisine'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ресторан"
        verbose_name_plural = "Рестораны"


class MenuItem(models.Model):
    history = HistoricalRecords()
    name = models.CharField(max_length=255, verbose_name="Название блюда")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(blank=True, null=True, verbose_name="Описание блюда")
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="Ресторан",
    )
    is_available = models.BooleanField(default=True, verbose_name="Доступно ли блюдо")
    image = models.ImageField(
        upload_to="menu_images/",
        blank=True,
        null=True,
        verbose_name="Изображение блюда",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
    )

    def __str__(self):
        return f"Блюдо {self.name} из ресторана {self.restaurant.name}"

    class Meta:
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"


class Order(models.Model):
    history = HistoricalRecords()
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("preparing", "Готовится"),
        ("delivering", "Доставляется"),
        ("completed", "Завершён"),
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
    link_dogovor = models.URLField(null=True, blank=True, verbose_name="Договор ссылка")
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
        self.total_price = sum(item.price for item in self.order_items.all())

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
        ordering = ["total_price"]


class OrderMenuItem(models.Model):
    history = HistoricalRecords()

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Заказ",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Блюдо",
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

class CourierQuerySet(models.QuerySet):
    def by_vehicle_type(self, vehicle_type):
        return self.filter(vehicle_type=vehicle_type)

    def with_vehicle_types(self, vehicle_types):
        if vehicle_types:
            return self.filter(vehicle_type__in=vehicle_types.split(','))
        return self

    def with_first_name_starts_with(self, first_name_starts_with):
        if first_name_starts_with:
            return self.filter(user__first_name__startswith=first_name_starts_with)
        return self

    def exclude_last_name_contains(self, exclude_last_name_contains):
        if exclude_last_name_contains:
            return self.exclude(user__last_name__icontains=exclude_last_name_contains)
        return self


class CourierManager(models.Manager):
    def get_queryset(self):
        return CourierQuerySet(self.model, using=self._db)

    def by_vehicle_type(self, vehicle_type):
        return self.get_queryset().by_vehicle_type(vehicle_type)

    def filtered(self, vehicle_types=None, first_name_starts_with=None, exclude_last_name_contains=None):
        """
        Функция применяет цепочку фильтров для фильтрации курьеров.
        """
        return (
            self.get_queryset()
            .with_vehicle_types(vehicle_types)
            .with_first_name_starts_with(first_name_starts_with)
            .exclude_last_name_contains(exclude_last_name_contains)
        )



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

    documents = models.FileField(upload_to='documents/', blank=True, null=True)

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