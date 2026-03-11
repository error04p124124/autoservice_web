from django import forms
from django.forms import ModelForm
from .models import Client, Car, Supplier, Service, SparePart, WorkOrder, WorkOrderService, WorkOrderPart, User

class ClientForm(ModelForm):
    class Meta:
        model = Client
        fields = ["full_name", "phone", "email", "passport"]

class CarForm(ModelForm):
    class Meta:
        model = Car
        fields = ["client", "vin", "brand", "model", "year", "license_plate", "mileage"]

class SupplierForm(ModelForm):
    class Meta:
        model = Supplier
        fields = ["company_name", "contact_phone", "email", "address"]

class ServiceForm(ModelForm):
    class Meta:
        model = Service
        fields = ["service_name", "category", "labor_hours", "hour_rate"]

class SparePartForm(ModelForm):
    class Meta:
        model = SparePart
        fields = ["article", "part_name", "manufacturer", "purchase_price", "sale_price", "quantity", "min_stock", "supplier"]

class WorkOrderForm(ModelForm):
    class Meta:
        model = WorkOrder
        fields = ["car", "mechanic", "status", "description"]

class WorkOrderServiceForm(ModelForm):
    class Meta:
        model = WorkOrderService
        fields = ["service", "qty"]

class WorkOrderPartForm(ModelForm):
    class Meta:
        model = WorkOrderPart
        fields = ["part", "qty"]

class UserCreateForm(ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "full_name", "phone", "role", "is_active", "is_staff"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
