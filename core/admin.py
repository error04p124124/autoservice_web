from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "phone", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "full_name", "phone")

admin.site.register(Client)
admin.site.register(Car)
admin.site.register(Supplier)
admin.site.register(Service)
admin.site.register(SparePart)
admin.site.register(WorkOrder)
admin.site.register(WorkOrderService)
admin.site.register(WorkOrderPart)
