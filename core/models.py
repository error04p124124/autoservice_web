from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Администратор"
        MANAGER = "manager", "Менеджер"
        MECHANIC = "mechanic", "Автомеханик"

    full_name = models.CharField("ФИО", max_length=100, blank=True, default="")
    phone = models.CharField("Телефон", max_length=20, blank=True, default="")
    role = models.CharField("Роль", max_length=20, choices=Role.choices, default=Role.MANAGER)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Client(models.Model):
    full_name = models.CharField("ФИО", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", max_length=100, blank=True, null=True)
    passport = models.CharField("Паспорт", max_length=11)

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class Car(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cars", verbose_name="Клиент")
    vin = models.CharField("VIN", max_length=17)
    brand = models.CharField("Марка", max_length=50)
    model = models.CharField("Модель", max_length=50)
    year = models.PositiveIntegerField("Год")
    license_plate = models.CharField("Гос. номер", max_length=12)
    mileage = models.PositiveIntegerField("Пробег", default=0)

    def __str__(self):
        return f"{self.brand} {self.model} [{self.license_plate}]"


class Supplier(models.Model):
    company_name = models.CharField("Компания", max_length=100)
    contact_phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", max_length=100, blank=True, null=True)
    address = models.CharField("Адрес", max_length=200, blank=True, default="")

    def __str__(self):
        return self.company_name


class Service(models.Model):
    service_name = models.CharField("Услуга", max_length=100)
    category = models.CharField("Категория", max_length=50)
    labor_hours = models.FloatField("Нормо-часы", validators=[MinValueValidator(0.0)])
    hour_rate = models.DecimalField("Ставка/час", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    @property
    def cost(self) -> float:
        return float(self.labor_hours) * float(self.hour_rate)

    def __str__(self):
        return self.service_name


class SparePart(models.Model):
    article = models.CharField("Артикул", max_length=50)
    part_name = models.CharField("Название", max_length=100)
    manufacturer = models.CharField("Производитель", max_length=50)
    purchase_price = models.DecimalField("Цена закупки", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    sale_price = models.DecimalField("Цена продажи", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField("Количество", default=0)
    min_stock = models.PositiveIntegerField("Мин. остаток", default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Поставщик")

    def is_low_stock(self) -> bool:
        return self.quantity <= self.min_stock

    def __str__(self):
        return f"{self.part_name} ({self.article})"


class WorkOrder(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        IN_PROGRESS = "in_progress", "В работе"
        WAITING_PARTS = "waiting_parts", "Ожидает запчастей"
        READY = "ready", "Готов"
        ISSUED = "issued", "Выдан"

    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name="orders", verbose_name="Автомобиль")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders_created", verbose_name="Создал")
    mechanic = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders_assigned",
        null=True,
        blank=True,
        limit_choices_to={"role": User.Role.MECHANIC},
        verbose_name="Исполнитель",
    )
    created_date = models.DateTimeField("Дата создания", auto_now_add=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.CREATED)
    description = models.TextField("Описание/неисправность", blank=True, null=True)

    services = models.ManyToManyField(Service, through="WorkOrderService", related_name="workorders")
    parts = models.ManyToManyField(SparePart, through="WorkOrderPart", related_name="workorders")

    def __str__(self):
        return f"Заказ-наряд #{self.id} ({self.get_status_display()})"

    @property
    def total_amount(self) -> float:
        services_sum = sum(x.line_total for x in self.workorderservice_set.select_related("service").all())
        parts_sum = sum(x.line_total for x in self.workorderpart_set.select_related("part").all())
        return float(services_sum + parts_sum)


class WorkOrderService(models.Model):
    workorder = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, verbose_name="Заказ-наряд")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    qty = models.PositiveIntegerField("Кол-во", default=1)

    class Meta:
        unique_together = ("workorder", "service")

    @property
    def line_total(self) -> float:
        return float(self.qty) * float(self.service.cost)

    def __str__(self):
        return f"{self.service} x{self.qty}"


class WorkOrderPart(models.Model):
    workorder = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, verbose_name="Заказ-наряд")
    part = models.ForeignKey(SparePart, on_delete=models.PROTECT, verbose_name="Запчасть")
    qty = models.PositiveIntegerField("Кол-во", default=1)

    class Meta:
        unique_together = ("workorder", "part")

    @property
    def line_total(self) -> float:
        return float(self.qty) * float(self.part.sale_price)

    def save(self, *args, **kwargs):
        # при первом добавлении списываем со склада
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # минимальная защита от отрицательного остатка
            self.part.quantity = max(0, int(self.part.quantity) - int(self.qty))
            self.part.save(update_fields=["quantity"])

    def __str__(self):
        return f"{self.part} x{self.qty}"
