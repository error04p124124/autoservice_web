from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("dash/manager/", views.dashboard_manager, name="dashboard_manager"),
    path("dash/mechanic/", views.dashboard_mechanic, name="dashboard_mechanic"),
    path("dash/admin/", views.dashboard_admin, name="dashboard_admin"),

    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:pk>/toggle/", views.user_toggle_active, name="user_toggle_active"),

    path("clients/", views.client_list, name="client_list"),
    path("clients/new/", views.client_create, name="client_create"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),

    path("cars/", views.car_list, name="car_list"),
    path("cars/new/", views.car_create, name="car_create"),
    path("cars/<int:pk>/edit/", views.car_edit, name="car_edit"),

    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/new/", views.supplier_create, name="supplier_create"),
    path("suppliers/<int:pk>/edit/", views.supplier_edit, name="supplier_edit"),

    path("services/", views.service_list, name="service_list"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),

    path("parts/", views.part_list, name="part_list"),
    path("parts/new/", views.part_create, name="part_create"),
    path("parts/<int:pk>/edit/", views.part_edit, name="part_edit"),

    path("orders/", views.workorder_list, name="workorder_list"),
    path("orders/new/", views.workorder_create, name="workorder_create"),
    path("orders/<int:pk>/", views.workorder_detail, name="workorder_detail"),
    path("orders/<int:pk>/edit/", views.workorder_edit, name="workorder_edit"),
    path("orders/<int:pk>/pdf/", views.workorder_pdf_view, name="workorder_pdf"),
    path("orders/<int:pk>/status/<str:status>/", views.workorder_set_status, name="workorder_set_status"),
    path("orders/<int:pk>/add-service/", views.workorder_add_service, name="workorder_add_service"),
    path("orders/<int:pk>/add-part/", views.workorder_add_part, name="workorder_add_part"),

    path("reports/", views.reports, name="reports"),
]
