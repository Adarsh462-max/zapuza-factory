
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class Machine(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    location = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Inspection(models.Model):
    RESULT_CHOICES = [
        ("PASS", "Pass"),
        ("FAIL", "Fail"),
    ]

    REVIEW_CHOICES = [
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    machine = models.ForeignKey(
        Machine, on_delete=models.PROTECT
    )
    part_number = models.CharField(max_length=50)
    nominal_value = models.DecimalField(
        max_digits=10, decimal_places=3
    )
    lower_limit = models.DecimalField(
        max_digits=10, decimal_places=3
    )
    upper_limit = models.DecimalField(
        max_digits=10, decimal_places=3
    )
    actual_value = models.DecimalField(
        max_digits=10, decimal_places=3
    )
    defect_photo = models.ImageField(
        upload_to="defects/", blank=True, null=True
    )

    result = models.CharField(
        max_length=10, choices=RESULT_CHOICES, blank=True
    )
    review_status = models.CharField(
        max_length=10,
        choices=REVIEW_CHOICES,
        default="PENDING",
    )
    supervisor_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.result = (
            "PASS"
            if self.lower_limit <= self.actual_value <= self.upper_limit
            else "FAIL"
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_number} - {self.result}"


class Dispatch(models.Model):
    inspection = models.OneToOneField(
        Inspection, on_delete=models.PROTECT
    )
    gate_pass_number = models.CharField(
        max_length=40, unique=True, blank=True
    )
    customer_name = models.CharField(max_length=100)
    cleared_at = models.DateTimeField(
        default=timezone.now
    )

    def save(self, *args, **kwargs):
        if (
            self.inspection.result != "PASS"
            or self.inspection.review_status != "APPROVED"
        ):
            raise ValueError(
                "Dispatch requires PASS and supervisor approval."
            )

        if not self.gate_pass_number:
            self.gate_pass_number = (
                f"ZAP-{timezone.now():%Y%m%d%H%M%S}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.gate_pass_number or "New Dispatch"


class RawMaterialIntake(models.Model):
    STATUS_CHOICES = [
        ("PENDING_VERIFICATION", "Pending Verification"),
        ("IN_LAB_TESTING", "In Lab Testing"),
        ("RELEASED", "Released"),
        ("SUPPLIER_QUARANTINE", "Supplier Quarantine"),
    ]

    supplier_name = models.CharField(max_length=150)
    purchase_order_number = models.CharField(max_length=100)
    material_grade = models.CharField(max_length=100)
    heat_number = models.CharField(max_length=100)
    quantity_received = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    mtc_file = models.FileField(
        upload_to="mtc_certificates/"
    )

    heat_number_verified = models.BooleanField(default=False)
    mtc_verified = models.BooleanField(default=False)
    lab_testing_required = models.BooleanField(default=False)
    lab_test_passed = models.BooleanField(default=False)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING_VERIFICATION",
    )

    verification_notes = models.TextField(blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if self.status == "RELEASED":
            if not self.mtc_file:
                raise ValidationError({
                    "mtc_file": "MTC document is required for release."
                })

            if not self.mtc_verified:
                raise ValidationError({
                    "mtc_verified": "Verify the MTC before releasing material."
                })

            if not self.heat_number_verified:
                raise ValidationError({
                    "heat_number_verified": (
                        "Verify the heat number before releasing material."
                    )
                })

            if self.lab_testing_required and not self.lab_test_passed:
                raise ValidationError({
                   "status": (
                   "Material cannot be released until laboratory testing passes."
                     )
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.heat_number} - {self.material_grade}"