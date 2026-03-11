from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from .models import User, Client, Car, Supplier, Service, SparePart, WorkOrder, WorkOrderService, WorkOrderPart
from .forms import (
    ClientForm, CarForm, SupplierForm, ServiceForm, SparePartForm, WorkOrderForm,
    WorkOrderServiceForm, WorkOrderPartForm, UserCreateForm
)
from .permissions import role_required
from .pdf import workorder_pdf

@login_required
def home(request):
    if request.user.is_superuser or request.user.role == User.Role.ADMIN:
        return redirect("dashboard_admin")
    if request.user.role == User.Role.MECHANIC:
        return redirect("dashboard_mechanic")
    return redirect("dashboard_manager")

@role_required(User.Role.MANAGER, User.Role.ADMIN)
def dashboard_manager(request):
    orders = WorkOrder.objects.select_related("car", "car__client").order_by("-created_date")[:12]
    by_status = WorkOrder.objects.values("status").annotate(cnt=Count("id")).order_by("status")
    low_stock = [p for p in SparePart.objects.all() if p.is_low_stock()][:10]
    return render(request, "dashboards/manager.html", {"orders": orders, "by_status": by_status, "low_stock": low_stock})

@role_required(User.Role.MECHANIC, User.Role.ADMIN)
def dashboard_mechanic(request):
    orders = WorkOrder.objects.select_related("car", "car__client").filter(mechanic=request.user).exclude(status=WorkOrder.Status.ISSUED).order_by("-created_date")
    return render(request, "dashboards/mechanic.html", {"orders": orders})

@role_required(User.Role.ADMIN)
def dashboard_admin(request):
    total_orders = WorkOrder.objects.count()
    total_clients = Client.objects.count()
    low_stock_count = sum(1 for p in SparePart.objects.all() if p.is_low_stock())
    return render(request, "dashboards/admin.html", {
        "total_orders": total_orders,
        "total_clients": total_clients,
        "low_stock_count": low_stock_count
    })

# --------- helper: search ---------
def _search_q(request):
    return (request.GET.get("q") or "").strip()

# --------- Users (admin only) ---------
@role_required(User.Role.ADMIN)
def user_list(request):
    q = _search_q(request)
    qs = User.objects.all().order_by("username")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(full_name__icontains=q) | Q(phone__icontains=q))
    return render(request, "core/user_list.html", {"items": qs, "q": q})

@role_required(User.Role.ADMIN)
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Пользователь создан")
            return redirect("user_list")
    else:
        form = UserCreateForm()
    return render(request, "core/form.html", {"title": "Создать пользователя", "form": form})

@role_required(User.Role.ADMIN)
def user_toggle_active(request, pk: int):
    u = get_object_or_404(User, pk=pk)
    if u == request.user:
        messages.warning(request, "Нельзя отключить самого себя")
        return redirect("user_list")
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    return redirect("user_list")

# --------- Clients ---------
@role_required(User.Role.MANAGER, User.Role.ADMIN)
def client_list(request):
    q = _search_q(request)
    qs = Client.objects.all().order_by("full_name")
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(passport__icontains=q))
    return render(request, "core/client_list.html", {"items": qs, "q": q})

@role_required(User.Role.MANAGER, User.Role.ADMIN)
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Клиент добавлен")
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(request, "core/form.html", {"title": "Новый клиент", "form": form})

@role_required(User.Role.MANAGER, User.Role.ADMIN)
def client_edit(request, pk: int):
    obj = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect("client_list")
    else:
        form = ClientForm(instance=obj)
    return render(request, "core/form.html", {"title": f"Редактировать клиента #{obj.id}", "form": form})

# --------- Cars ---------
@role_required(User.Role.MANAGER, User.Role.ADMIN)
def car_list(request):
    q = _search_q(request)
    qs = Car.objects.select_related("client").all().order_by("-id")
    if q:
        qs = qs.filter(Q(license_plate__icontains=q) | Q(vin__icontains=q) | Q(client__full_name__icontains=q))
    return render(request, "core/car_list.html", {"items": qs, "q": q})

@role_required(User.Role.MANAGER, User.Role.ADMIN)
def car_create(request):
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Автомобиль добавлен")
            return redirect("car_list")
    else:
        form = CarForm()
    return render(request, "core/form.html", {"title": "Новый автомобиль", "form": form})

@role_required(User.Role.MANAGER, User.Role.ADMIN)
def car_edit(request, pk: int):
    obj = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect("car_list")
    else:
        form = CarForm(instance=obj)
    return render(request, "core/form.html", {"title": f"Редактировать авто #{obj.id}", "form": form})

# --------- Suppliers ---------
@role_required(User.Role.ADMIN)
def supplier_list(request):
    q = _search_q(request)
    qs = Supplier.objects.all().order_by("company_name")
    if q:
        qs = qs.filter(Q(company_name__icontains=q) | Q(contact_phone__icontains=q))
    return render(request, "core/supplier_list.html", {"items": qs, "q": q})

@role_required(User.Role.ADMIN)
def supplier_create(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Поставщик добавлен")
            return redirect("supplier_list")
    else:
        form = SupplierForm()
    return render(request, "core/form.html", {"title": "Новый поставщик", "form": form})

@role_required(User.Role.ADMIN)
def supplier_edit(request, pk: int):
    obj = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect("supplier_list")
    else:
        form = SupplierForm(instance=obj)
    return render(request, "core/form.html", {"title": f"Редактировать поставщика #{obj.id}", "form": form})

# --------- Services ---------
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def service_list(request):
    q = _search_q(request)
    qs = Service.objects.all().order_by("service_name")
    if q:
        qs = qs.filter(Q(service_name__icontains=q) | Q(category__icontains=q))
    return render(request, "core/service_list.html", {"items": qs, "q": q})

@role_required(User.Role.ADMIN)
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Услуга добавлена")
            return redirect("service_list")
    else:
        form = ServiceForm()
    return render(request, "core/form.html", {"title": "Новая услуга", "form": form})

@role_required(User.Role.ADMIN)
def service_edit(request, pk: int):
    obj = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect("service_list")
    else:
        form = ServiceForm(instance=obj)
    return render(request, "core/form.html", {"title": f"Редактировать услугу #{obj.id}", "form": form})

# --------- Parts ---------
@role_required(User.Role.ADMIN, User.Role.MANAGER)
def part_list(request):
    q = _search_q(request)
    qs = SparePart.objects.select_related("supplier").all().order_by("part_name")
    if q:
        qs = qs.filter(Q(part_name__icontains=q) | Q(article__icontains=q) | Q(manufacturer__icontains=q))
    return render(request, "core/part_list.html", {"items": qs, "q": q})

@role_required(User.Role.ADMIN)
def part_create(request):
    if request.method == "POST":
        form = SparePartForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Запчасть добавлена")
            return redirect("part_list")
    else:
        form = SparePartForm()
    return render(request, "core/form.html", {"title": "Новая запчасть", "form": form})

@role_required(User.Role.ADMIN)
def part_edit(request, pk: int):
    obj = get_object_or_404(SparePart, pk=pk)
    if request.method == "POST":
        form = SparePartForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect("part_list")
    else:
        form = SparePartForm(instance=obj)
    return render(request, "core/form.html", {"title": f"Редактировать запчасть #{obj.id}", "form": form})

# --------- WorkOrders ---------
@role_required(User.Role.ADMIN, User.Role.MANAGER, User.Role.MECHANIC)
def workorder_list(request):
    q = _search_q(request)
    qs = WorkOrder.objects.select_related("car", "car__client", "mechanic").all().order_by("-created_date")
    if request.user.role == User.Role.MECHANIC and not request.user.is_superuser:
        qs = qs.filter(mechanic=request.user)

    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(car__license_plate__icontains=q) |
            Q(car__vin__icontains=q) |
            Q(car__client__full_name__icontains=q)
        )
    return render(request, "core/workorder_list.html", {"items": qs, "q": q})

@role_required(User.Role.MANAGER, User.Role.ADMIN)
def workorder_create(request):
    if request.method == "POST":
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f"Заказ-наряд #{obj.id} создан")
            return redirect("workorder_detail", pk=obj.pk)
    else:
        form = WorkOrderForm(initial={"status": WorkOrder.Status.CREATED})
    return render(request, "core/form.html", {"title": "Новый заказ-наряд", "form": form})

@role_required(User.Role.ADMIN, User.Role.MANAGER, User.Role.MECHANIC)
def workorder_detail(request, pk: int):
    wo = get_object_or_404(WorkOrder.objects.select_related("car", "car__client", "mechanic"), pk=pk)
    if request.user.role == User.Role.MECHANIC and not request.user.is_superuser:
        if wo.mechanic_id != request.user.id:
            raise Http404()

    service_form = WorkOrderServiceForm()
    part_form = WorkOrderPartForm()
    return render(request, "core/workorder_detail.html", {
        "wo": wo,
        "service_form": service_form,
        "part_form": part_form,
    })

@role_required(User.Role.ADMIN, User.Role.MANAGER)
def workorder_edit(request, pk: int):
    wo = get_object_or_404(WorkOrder, pk=pk)
    if request.method == "POST":
        form = WorkOrderForm(request.POST, instance=wo)
        if form.is_valid():
            form.save()
            messages.success(request, "Заказ-наряд обновлен")
            return redirect("workorder_detail", pk=pk)
    else:
        form = WorkOrderForm(instance=wo)
    return render(request, "core/form.html", {"title": f"Редактировать заказ-наряд #{wo.id}", "form": form})

@role_required(User.Role.ADMIN, User.Role.MANAGER, User.Role.MECHANIC)
def workorder_set_status(request, pk: int, status: str):
    wo = get_object_or_404(WorkOrder, pk=pk)
    allowed = {s for s, _ in WorkOrder.Status.choices}
    if status not in allowed:
        raise Http404()

    # механик может менять только свой заказ
    if request.user.role == User.Role.MECHANIC and not request.user.is_superuser:
        if wo.mechanic_id != request.user.id:
            raise Http404()

    wo.status = status
    wo.save(update_fields=["status"])
    return redirect("workorder_detail", pk=pk)

@role_required(User.Role.ADMIN, User.Role.MANAGER)
def workorder_add_service(request, pk: int):
    wo = get_object_or_404(WorkOrder, pk=pk)
    if request.method != "POST":
        return redirect("workorder_detail", pk=pk)
    form = WorkOrderServiceForm(request.POST)
    if form.is_valid():
        ws = form.save(commit=False)
        ws.workorder = wo
        ws.save()
        messages.success(request, "Услуга добавлена")
    else:
        messages.error(request, "Ошибка добавления услуги")
    return redirect("workorder_detail", pk=pk)

@role_required(User.Role.ADMIN, User.Role.MANAGER, User.Role.MECHANIC)
def workorder_add_part(request, pk: int):
    wo = get_object_or_404(WorkOrder, pk=pk)
    if request.method != "POST":
        return redirect("workorder_detail", pk=pk)

    # механик может добавлять запчасти только в свой заказ
    if request.user.role == User.Role.MECHANIC and not request.user.is_superuser:
        if wo.mechanic_id != request.user.id:
            raise Http404()

    form = WorkOrderPartForm(request.POST)
    if form.is_valid():
        wp = form.save(commit=False)
        wp.workorder = wo
        wp.save()  # здесь автоматически спишется склад
        messages.success(request, "Запчасть добавлена (остаток списан)")
    else:
        messages.error(request, "Ошибка добавления запчасти")
    return redirect("workorder_detail", pk=pk)

@role_required(User.Role.ADMIN, User.Role.MANAGER)
def workorder_pdf_view(request, pk: int):
    wo = get_object_or_404(WorkOrder.objects.select_related("car", "car__client"), pk=pk)
    data = workorder_pdf(wo)
    resp = HttpResponse(data, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="workorder_{wo.id}.pdf"'
    return resp

# --------- Reports (admin) ---------
@role_required(User.Role.ADMIN)
def reports(request):
    by_status = WorkOrder.objects.values("status").annotate(cnt=Count("id")).order_by("status")
    top_services = (
        WorkOrderService.objects.values("service__service_name")
        .annotate(qty=Sum("qty"))
        .order_by("-qty")[:10]
    )
    top_parts = (
        WorkOrderPart.objects.values("part__part_name")
        .annotate(qty=Sum("qty"))
        .order_by("-qty")[:10]
    )
    return render(request, "core/reports.html", {
        "by_status": by_status,
        "top_services": top_services,
        "top_parts": top_parts,
    })
