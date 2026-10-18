

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Machine Management
    path("machines/", views.machine_list, name="machine_list"),
    path("machines/add/", views.machine_create, name="machine_create"),
    path(
        "machines/<int:pk>/toggle/",
        views.machine_toggle,
        name="machine_toggle",
    ),

    # Quality Inspection
    path("inspections/", views.inspection_list, name="inspection_list"),
    path(
        "inspections/add/",
        views.inspection_create,
        name="inspection_create",
    ),

    # Supervisor Approval
    path("approvals/", views.approval_list, name="approval_list"),
    path(
        "approvals/<int:pk>/",
        views.review_inspection,
        name="review_inspection",
    ),

    # Dispatch Clearance
    path("dispatch/", views.dispatch_list, name="dispatch_list"),
    path(
        "dispatch/add/",
        views.dispatch_create,
        name="dispatch_create",
    ),

    # Raw Material Intake
    path(
        "raw-material/",
        views.raw_material_list,
        name="raw_material_list",
    ),
    path(
        "raw-material/add/",
        views.raw_material_create,
        name="raw_material_create",
    ),

    path(
    "raw-material/<int:pk>/verify/",
    views.raw_material_verify,
    name="raw_material_verify",
),
path(
    "raw-material/<int:pk>/lab-result/",
    views.raw_material_lab_result,
    name="raw_material_lab_result",
),
path(
    "raw-material/<int:pk>/release/",
    views.raw_material_release,
    name="raw_material_release",
),
path(
    "raw-material/<int:pk>/quarantine/",
    views.raw_material_quarantine,
    name="raw_material_quarantine",
),
]