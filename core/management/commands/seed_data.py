from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    User, Client, Car, Supplier, Service, SparePart, WorkOrder,
    WorkOrderService, WorkOrderPart,
)


USERS = [
    dict(
        username="admin",
        password="Admin1234!",
        full_name="Иванов Иван Иванович",
        phone="+7 900 000-00-01",
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True,
        email="admin@autoservice.local",
    ),
    dict(
        username="manager",
        password="Manager1234!",
        full_name="Петрова Анна Сергеевна",
        phone="+7 900 000-00-02",
        role=User.Role.MANAGER,
        email="manager@autoservice.local",
    ),
    dict(
        username="mechanic",
        password="Mechanic1234!",
        full_name="Сидоров Алексей Викторович",
        phone="+7 900 000-00-03",
        role=User.Role.MECHANIC,
        email="mechanic@autoservice.local",
    ),
]


class Command(BaseCommand):
    help = "Populate the database with demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Создание пользователей...")
        users = {}
        for data in USERS:
            pw = data.pop("password")
            obj, created = User.objects.update_or_create(
                username=data["username"], defaults=data
            )
            obj.set_password(pw)
            obj.save()
            users[data["username"]] = obj
            status = "создан" if created else "обновлён"
            self.stdout.write(f"  [{status}] {obj.username}")

        self.stdout.write("Создание поставщиков...")
        supplier, _ = Supplier.objects.get_or_create(
            company_name="АвтоДеталь Плюс",
            defaults=dict(
                contact_phone="+7 495 123-45-67",
                email="supply@autodetalplus.ru",
                address="Москва, ул. Промышленная, 5",
            ),
        )

        self.stdout.write("Создание услуг...")
        services_data = [
            dict(service_name="Замена масла", category="ТО", labor_hours=0.5, hour_rate=1500),
            dict(service_name="Замена тормозных колодок", category="Тормоза", labor_hours=1.5, hour_rate=1500),
            dict(service_name="Диагностика двигателя", category="Диагностика", labor_hours=1.0, hour_rate=1800),
            dict(service_name="Развал-схождение", category="Ходовая", labor_hours=1.0, hour_rate=1200),
        ]
        services = []
        for sd in services_data:
            svc, _ = Service.objects.get_or_create(service_name=sd["service_name"], defaults=sd)
            services.append(svc)

        self.stdout.write("Создание запчастей...")
        parts_data = [
            dict(article="OIL-5W40-4L", part_name="Масло моторное 5W-40 4л", manufacturer="Castrol",
                 purchase_price=900, sale_price=1200, quantity=50, min_stock=10, supplier=supplier),
            dict(article="BP-FRONT-VAZ", part_name="Колодки тормозные передние", manufacturer="Ferodo",
                 purchase_price=600, sale_price=900, quantity=20, min_stock=5, supplier=supplier),
            dict(article="FILTER-OIL-01", part_name="Фильтр масляный", manufacturer="Bosch",
                 purchase_price=200, sale_price=350, quantity=30, min_stock=8, supplier=supplier),
        ]
        parts = []
        for pd in parts_data:
            part, _ = SparePart.objects.get_or_create(article=pd["article"], defaults=pd)
            parts.append(part)

        self.stdout.write("Создание клиентов и автомобилей...")
        clients_data = [
            dict(full_name="Кузнецов Дмитрий Олегович", phone="+7 916 111-22-33",
                 email="kuznetsov@mail.ru", passport="4512345678"),
            dict(full_name="Морозова Екатерина Павловна", phone="+7 926 444-55-66",
                 email="morozova@mail.ru", passport="4613654321"),
        ]
        cars_data = [
            dict(vin="XTA210930X2456789", brand="Lada", model="Vesta", year=2021,
                 license_plate="А123БВ77", mileage=45000),
            dict(vin="X9LFSR830LG123456", brand="Kia", model="Rio", year=2020,
                 license_plate="В456ГД99", mileage=62000),
        ]
        cars = []
        for i, cd in enumerate(clients_data):
            client, _ = Client.objects.get_or_create(passport=cd["passport"], defaults=cd)
            car_d = cars_data[i]
            car, _ = Car.objects.get_or_create(vin=car_d["vin"], defaults={**car_d, "client": client})
            cars.append(car)

        self.stdout.write("Создание заказ-нарядов...")
        manager = users["manager"]
        mechanic = users["mechanic"]

        wo1, created = WorkOrder.objects.get_or_create(
            car=cars[0],
            created_by=manager,
            defaults=dict(mechanic=mechanic, status=WorkOrder.Status.IN_PROGRESS,
                          description="Плановое ТО: замена масла и фильтра"),
        )
        if created:
            WorkOrderService.objects.get_or_create(workorder=wo1, service=services[0])
            WorkOrderPart.objects.get_or_create(workorder=wo1, part=parts[0], defaults={"qty": 1})
            WorkOrderPart.objects.get_or_create(workorder=wo1, part=parts[2], defaults={"qty": 1})

        wo2, created = WorkOrder.objects.get_or_create(
            car=cars[1],
            created_by=manager,
            defaults=dict(mechanic=mechanic, status=WorkOrder.Status.READY,
                          description="Замена передних тормозных колодок"),
        )
        if created:
            WorkOrderService.objects.get_or_create(workorder=wo2, service=services[1])
            WorkOrderPart.objects.get_or_create(workorder=wo2, part=parts[1], defaults={"qty": 1})

        self.stdout.write(self.style.SUCCESS("\nТестовые данные успешно загружены!"))
