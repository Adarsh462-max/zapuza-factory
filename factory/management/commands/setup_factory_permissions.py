
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


ROLE_PERMISSIONS = {
    "Admin": None,

    "Quality Engineer": {
        "view_machine",
        "view_rawmaterialintake",
        "add_rawmaterialintake",
        "change_rawmaterialintake",
        "view_inspection",
        "add_inspection",
        "change_inspection",
    },

    "Quality Manager": {
        "view_machine",
        "view_rawmaterialintake",
        "change_rawmaterialintake",
        "view_inspection",
        "change_inspection",
        "view_dispatch",
    },

    "Shift Supervisor": {
        "view_machine",
        "view_inspection",
        "add_inspection",
        "change_inspection",
    },

    "Dispatch Operator": {
        "view_machine",
        "view_inspection",
        "view_dispatch",
        "add_dispatch",
    },
}


class Command(BaseCommand):
    help = "Assign Django permissions to Zapuza factory roles"

    def handle(self, *args, **options):
        factory_permissions = Permission.objects.filter(
            content_type__app_label="factory"
        )

        for role_name, allowed_codes in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)

            if allowed_codes is None:
                # Admin gets all factory model permissions.
                group.permissions.set(factory_permissions)
            else:
                permissions = Permission.objects.filter(
                    content_type__app_label="factory",
                    codename__in=allowed_codes,
                )

                found_codes = set(
                    permissions.values_list("codename", flat=True)
                )
                missing_codes = allowed_codes - found_codes

                if missing_codes:
                    self.stdout.write(
                        self.style.WARNING(
                            f"{role_name}: missing permissions "
                            f"{sorted(missing_codes)}"
                        )
                    )

                group.permissions.set(permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Permissions assigned to {role_name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Factory permission setup completed."
            )
        )
