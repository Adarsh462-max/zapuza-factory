from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from functools import wraps


from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Machine, Inspection, Dispatch, RawMaterialIntake
from django.core.exceptions import ValidationError



# =========================
# ROLE-BASED ACCESS CONTROL
# =========================

def role_required(*allowed_roles):
    """
    Allow access only to authenticated users who have
    one of the specified factory roles, or are superusers.
    """
    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            has_role = request.user.groups.filter(
                name__in=allowed_roles
            ).exists()

            if not has_role:
                raise PermissionDenied(
                    "You do not have permission to access this action."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator



# =========================
# 1. DASHBOARD
# =========================
@login_required

def dashboard(request):
    context = {
        "total_machines": Machine.objects.count(),
        "active_machines": Machine.objects.filter(is_active=True).count(),
        "total_inspections": Inspection.objects.count(),
        "pending_reviews": Inspection.objects.filter(
            review_status="PENDING"
        ).count(),
        "approved_inspections": Inspection.objects.filter(
            review_status="APPROVED"
        ).count(),
        "failed_inspections": Inspection.objects.filter(
            result="FAIL"
        ).count(),
        "dispatch_count": Dispatch.objects.count(),
        "recent_inspections": Inspection.objects.select_related(
            "machine"
        ).order_by("-created_at")[:5],
    }

    return render(request, "factory/dashboard.html", context)


# =========================
# 2. MACHINE MANAGEMENT
# =========================
@login_required

def machine_list(request):
    machines = Machine.objects.all().order_by("code")

    return render(
        request,
        "factory/machine_list.html",
        {"machines": machines},
    )

@role_required("Admin")

def machine_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        location = request.POST.get("location", "").strip()

        if not name or not code or not location:
            messages.error(request, "All fields are required.")

        elif Machine.objects.filter(code=code).exists():
            messages.error(request, "Machine code already exists.")

        else:
            Machine.objects.create(
                name=name,
                code=code,
                location=location,
            )
            messages.success(request, "Machine added successfully.")
            return redirect("machine_list")

    return render(request, "factory/machine_form.html")

@role_required("Admin")
@require_POST
def machine_toggle(request, pk):
    machine = get_object_or_404(Machine, pk=pk)

    machine.is_active = not machine.is_active
    machine.save(update_fields=["is_active"])

    messages.success(
        request,
        f"{machine.code} status updated successfully.",
    )

    return redirect("machine_list")


# =========================
# 3. QUALITY INSPECTION
# =========================
@login_required
def inspection_list(request):
    inspections = Inspection.objects.select_related(
        "machine"
    ).order_by("-created_at")

    return render(
        request,
        "factory/inspection_list.html",
        {"inspections": inspections},
    )

@role_required("Quality Engineer", "Shift Supervisor")
def inspection_create(request):
    machines = Machine.objects.filter(is_active=True)

    if request.method == "POST":
        machine_id = request.POST.get("machine", "").strip()
        part_number = request.POST.get("part_number", "").strip()
        nominal = request.POST.get("nominal_value", "").strip()
        lower = request.POST.get("lower_limit", "").strip()
        upper = request.POST.get("upper_limit", "").strip()
        actual = request.POST.get("actual_value", "").strip()
        photo = request.FILES.get("defect_photo")

        try:
            if not part_number:
                raise ValueError("Part number is required.")

            machine = Machine.objects.get(
                pk=machine_id,
                is_active=True,
            )

            nominal_value = Decimal(nominal)
            lower_limit = Decimal(lower)
            upper_limit = Decimal(upper)
            actual_value = Decimal(actual)

            values = [
                nominal_value,
                lower_limit,
                upper_limit,
                actual_value,
            ]

            if not all(value.is_finite() for value in values):
                raise ValueError("Measurements must be finite numbers.")

            if lower_limit > upper_limit:
                raise ValueError(
                    "Lower limit cannot exceed upper limit."
                )

            if not lower_limit <= nominal_value <= upper_limit:
                raise ValueError(
                    "Nominal value must be within the tolerance limits."
                )

            result = (
                "PASS"
                if lower_limit <= actual_value <= upper_limit
                else "FAIL"
            )

            if result == "FAIL" and not photo:
                raise ValueError(
                    "A defect photo is required for a failed inspection."
                )

            inspection = Inspection(
                machine=machine,
                part_number=part_number,
                nominal_value=nominal_value,
                lower_limit=lower_limit,
                upper_limit=upper_limit,
                actual_value=actual_value,
                defect_photo=photo,
            )
            inspection.save()

            messages.success(
                request,
                f"Inspection saved successfully: {inspection.result}",
            )
            return redirect("inspection_list")

        except Machine.DoesNotExist:
            messages.error(request, "Select a valid active machine.")

        except (ValueError, InvalidOperation) as error:
            messages.error(request, str(error))

    return render(
        request,
        "factory/inspection_form.html",
        {"machines": machines},
    )


# =========================
# 4. SUPERVISOR APPROVAL
# =========================
@role_required("Quality Manager", "Shift Supervisor")
def approval_list(request):
    inspections = Inspection.objects.select_related(
        "machine"
    ).filter(
        review_status="PENDING"
    ).order_by("-created_at")

    return render(
        request,
        "factory/approval_list.html",
        {"inspections": inspections},
    )

@role_required("Quality Manager", "Shift Supervisor")
def review_inspection(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related("machine"),
        pk=pk,
    )

    if request.method == "POST":
        if inspection.review_status != "PENDING":
            messages.error(
                request,
                "This inspection has already been reviewed.",
            )
            return redirect("approval_list")

        action = request.POST.get("action", "")
        remark = request.POST.get("supervisor_remark", "").strip()

        if action == "approve":
            if inspection.result != "PASS":
                messages.error(
                    request,
                    "A failed inspection cannot be approved for normal dispatch.",
                )
                return redirect("approval_list")

            inspection.review_status = "APPROVED"

        elif action == "reject":
            if not remark:
                messages.error(
                    request,
                    "A remark is required when rejecting an inspection.",
                )
                return redirect("review_inspection", pk=pk)

            inspection.review_status = "REJECTED"

        else:
            messages.error(request, "Invalid review action.")
            return redirect("review_inspection", pk=pk)

        inspection.supervisor_remark = remark
        inspection.save(
            update_fields=[
                "review_status",
                "supervisor_remark",
            ]
        )

        messages.success(request, "Inspection review saved.")
        return redirect("approval_list")

    return render(
        request,
        "factory/review_inspection.html",
        {"inspection": inspection},
    )


# =========================
# 5. DISPATCH CLEARANCE
# =========================
@role_required("Dispatch Operator", "Quality Manager")
def dispatch_list(request):
    dispatches = Dispatch.objects.select_related(
        "inspection",
        "inspection__machine",
    ).order_by("-cleared_at")

    eligible_inspections = Inspection.objects.filter(
        result="PASS",
        review_status="APPROVED",
    ).exclude(
        dispatch__isnull=False
    ).select_related("machine").order_by("-created_at")

    return render(
        request,
        "factory/dispatch_list.html",
        {
            "dispatches": dispatches,
            "eligible_inspections": eligible_inspections,
        },
    )

@role_required("Dispatch Operator")
def dispatch_create(request):
    eligible_inspections = Inspection.objects.filter(
        result="PASS",
        review_status="APPROVED",
    ).exclude(
        dispatch__isnull=False
    ).select_related("machine")

    if request.method == "POST":
        inspection_id = request.POST.get("inspection", "").strip()
        customer_name = request.POST.get("customer_name", "").strip()

        if not customer_name:
            messages.error(request, "Customer name is required.")

        else:
            try:
                with transaction.atomic():
                    inspection = get_object_or_404(
                        Inspection.objects.select_for_update(),
                        pk=inspection_id,
                    )

                    if (
                        inspection.result != "PASS"
                        or inspection.review_status != "APPROVED"
                    ):
                        messages.error(
                            request,
                            "Only approved PASS inspections can be dispatched.",
                        )
                        return redirect("dispatch_list")

                    if Dispatch.objects.filter(
                        inspection=inspection
                    ).exists():
                        messages.error(
                            request,
                            "A dispatch record already exists for this inspection.",
                        )
                        return redirect("dispatch_list")

                    dispatch = Dispatch(
                        inspection=inspection,
                        customer_name=customer_name,
                    )
                    dispatch.save()

                messages.success(
                    request,
                    f"Dispatch clearance created: {dispatch.gate_pass_number}",
                )
                return redirect("dispatch_list")

            except Inspection.DoesNotExist:
                messages.error(request, "Select a valid inspection.")

            except (ValueError, IntegrityError):
                messages.error(
                    request,
                    "Dispatch could not be created. Check eligibility and try again.",
                )

    return render(
        request,
        "factory/dispatch_form.html",
        {"eligible_inspections": eligible_inspections},
    )

# =========================
# 6. RAW MATERIAL INTAKE
# =========================

@role_required("Quality Engineer", "Quality Manager")
def raw_material_list(request):
    materials = RawMaterialIntake.objects.all().order_by("-received_at")

    context = {
        "materials": materials,
        "pending_count": materials.filter(
            status="PENDING_VERIFICATION"
        ).count(),
        "lab_count": materials.filter(
            status="IN_LAB_TESTING"
        ).count(),
        "released_count": materials.filter(
            status="RELEASED"
        ).count(),
    }

    return render(
        request,
        "factory/raw_material_list.html",
        context,
    )


@role_required("Quality Engineer")
def raw_material_create(request):
    if request.method == "POST":
        supplier_name = request.POST.get("supplier_name", "").strip()
        purchase_order_number = request.POST.get(
            "purchase_order_number", ""
        ).strip()
        material_grade = request.POST.get("material_grade", "").strip()
        heat_number = request.POST.get("heat_number", "").strip()
        quantity = request.POST.get("quantity_received", "").strip()
        mtc_file = request.FILES.get("mtc_file")
        lab_testing_required = (
            request.POST.get("lab_testing_required") == "on"
        )

        try:
            if not all([
                supplier_name,
                purchase_order_number,
                material_grade,
                heat_number,
                quantity,
                mtc_file,
            ]):
                raise ValueError(
                    "All fields and the MTC document are required."
                )

            if len(supplier_name) > 150:
                raise ValueError("Supplier name is too long.")

            if len(purchase_order_number) > 100:
                raise ValueError("Purchase order number is too long.")

            if len(material_grade) > 100 or len(heat_number) > 100:
                raise ValueError("Material grade or heat number is too long.")

            quantity_received = int(quantity)

            if quantity_received < 1:
                raise ValueError("Quantity must be at least 1.")

            # Basic upload safeguards; actual MTC verification is a separate step.
            if mtc_file.size > 10 * 1024 * 1024:
                raise ValueError("MTC file must be 10 MB or smaller.")

            allowed_extensions = (".pdf", ".jpg", ".jpeg", ".png")
            if not mtc_file.name.lower().endswith(allowed_extensions):
                raise ValueError(
                    "Upload the MTC as a PDF, JPG, or PNG file."
                )

            material = RawMaterialIntake(
                supplier_name=supplier_name,
                purchase_order_number=purchase_order_number,
                material_grade=material_grade,
                heat_number=heat_number,
                quantity_received=quantity_received,
                mtc_file=mtc_file,
                lab_testing_required=lab_testing_required,
                status=(
                    "IN_LAB_TESTING"
                    if lab_testing_required
                    else "PENDING_VERIFICATION"
                ),
            )
            material.save()

            messages.success(
                request,
                "Raw material intake recorded. MTC and heat number "
                "verification are pending.",
            )
            return redirect("raw_material_list")

        except (ValueError, ValidationError) as error:
            messages.error(request, str(error))

    return render(request, "factory/raw_material_form.html")


# =========================
# 7. RAW MATERIAL VERIFICATION
# =========================
@role_required("Quality Engineer")
@require_POST
def raw_material_verify(request, pk):
    material = get_object_or_404(RawMaterialIntake, pk=pk)

    if material.status in ["RELEASED", "SUPPLIER_QUARANTINE"]:
        messages.error(
            request,
            "This material has already been finalized."
        )
        return redirect("raw_material_list")

    mtc_verified = request.POST.get("mtc_verified") == "on"
    heat_verified = request.POST.get("heat_number_verified") == "on"

    if not mtc_verified or not heat_verified:
        material.status = "SUPPLIER_QUARANTINE"
        material.verification_notes = (
            "Verification failed or incomplete. "
            "Material moved to supplier quarantine."
        )
        material.save()
        messages.error(
            request,
            "Both MTC and heat number must be verified. "
            "Material moved to quarantine."
        )
        return redirect("raw_material_list")

    material.mtc_verified = True
    material.heat_number_verified = True

    if material.lab_testing_required:
        if not material.lab_test_passed:
            material.status = "IN_LAB_TESTING"
        else:
            material.status = "PENDING_VERIFICATION"
    else:
        material.status = "PENDING_VERIFICATION"

    material.verification_notes = (
        "MTC and heat number verified."
    )
    material.save()

    messages.success(
        request,
        "MTC and heat number verification recorded."
    )
    return redirect("raw_material_list")

@role_required("Quality Engineer")
@require_POST
def raw_material_lab_result(request, pk):
    material = get_object_or_404(RawMaterialIntake, pk=pk)

    if material.status in ["RELEASED", "SUPPLIER_QUARANTINE"]:
        messages.error(
            request,
            "Lab result cannot be changed for finalized material."
        )
        return redirect("raw_material_list")

    if not material.lab_testing_required:
        messages.error(
            request,
            "Laboratory testing is not required for this material."
        )
        return redirect("raw_material_list")

    if not material.mtc_verified or not material.heat_number_verified:
        messages.error(
            request,
            "Verify the MTC and heat number before recording "
            "the lab result."
        )
        return redirect("raw_material_list")

    result = request.POST.get("lab_result")

    if result not in ["PASS", "FAIL"]:
        messages.error(request, "Select a valid lab result.")
        return redirect("raw_material_list")

    if result == "FAIL":
        material.lab_test_passed = False
        material.status = "SUPPLIER_QUARANTINE"
        material.verification_notes = "Laboratory test failed."
        material.save()
        messages.error(
            request,
            "Lab test failed. Material moved to supplier quarantine."
        )
    else:
        material.lab_test_passed = True
        material.status = "PENDING_VERIFICATION"
        material.verification_notes = "Laboratory test passed."
        material.save()
        messages.success(
            request,
            "Lab test passed. Material can now be considered for release."
        )

    return redirect("raw_material_list")

@role_required("Quality Manager")
@require_POST
def raw_material_release(request, pk):
    material = get_object_or_404(RawMaterialIntake, pk=pk)

    if material.status in ["RELEASED", "SUPPLIER_QUARANTINE"]:
        messages.error(
            request,
            "This material cannot be released from its current status."
        )
        return redirect("raw_material_list")

    if not material.mtc_verified or not material.heat_number_verified:
        messages.error(
            request,
            "MTC and heat number verification are required."
        )
        return redirect("raw_material_list")

    if material.lab_testing_required and not material.lab_test_passed:
        messages.error(
            request,
            "Laboratory testing must pass before release."
        )
        return redirect("raw_material_list")

    material.status = "RELEASED"
    material.verification_notes = "All required checks passed; material released."
    material.save()

    messages.success(
        request,
        "Raw material released successfully."
    )
    return redirect("raw_material_list")

@role_required("Quality Engineer", "Quality Manager")
@require_POST
def raw_material_quarantine(request, pk):
    material = get_object_or_404(RawMaterialIntake, pk=pk)

    if material.status == "RELEASED":
        messages.error(
            request,
            "Released material cannot be quarantined through this action."
        )
        return redirect("raw_material_list")

    reason = request.POST.get("reason", "").strip()

    if not reason:
        messages.error(
            request,
            "A quarantine reason is required."
        )
        return redirect("raw_material_list")

    material.status = "SUPPLIER_QUARANTINE"
    material.verification_notes = reason
    material.save()

    messages.warning(
        request,
        "Material moved to supplier quarantine."
    )
    return redirect("raw_material_list")
