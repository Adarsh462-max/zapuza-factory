
from django.contrib import admin
from .models import Machine, Inspection, Dispatch, RawMaterialIntake


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "location", "is_active")
    search_fields = ("code", "name", "location")
    list_filter = ("is_active",)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        "part_number",
        "machine",
        "actual_value",
        "result",
        "review_status",
        "created_at",
    )
    search_fields = ("part_number", "machine__code")
    list_filter = ("result", "review_status", "created_at")
    readonly_fields = ("result", "created_at")


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = (
        "gate_pass_number",
        "customer_name",
        "inspection",
        "cleared_at",
    )
    search_fields = ("gate_pass_number", "customer_name")
    readonly_fields = ("gate_pass_number", "cleared_at")


@admin.register(RawMaterialIntake)
class RawMaterialIntakeAdmin(admin.ModelAdmin):
    list_display = (
        "heat_number",
        "supplier_name",
        "material_grade",
        "quantity_received",
        "status",
        "mtc_verified",
        "heat_number_verified",
        "received_at",
    )

    search_fields = (
        "heat_number",
        "supplier_name",
        "purchase_order_number",
        "material_grade",
    )

    list_filter = (
        "status",
        "mtc_verified",
        "heat_number_verified",
        "lab_testing_required",
        "received_at",
    )

    readonly_fields = ("received_at", "updated_at")

    fieldsets = (
        ("Material Details", {
            "fields": (
                "supplier_name",
                "purchase_order_number",
                "material_grade",
                "heat_number",
                "quantity_received",
            )
        }),
        ("MTC Verification", {
            "fields": (
                "mtc_file",
                "mtc_verified",
                "heat_number_verified",
                "verification_notes",
            )
        }),
        ("Testing & Release", {
            "fields": (
                "lab_testing_required",
                "status",
            )
        }),
        ("Timestamps", {
            "fields": ("received_at", "updated_at")
        }),
    )
