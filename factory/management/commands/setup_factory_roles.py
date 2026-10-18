
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


FACTORY_ROLES = [
    "Admin",
    "Quality Engineer",
    "Quality Manager",
    "Shift Supervisor",
    "Dispatch Operator",
]


class Command(BaseCommand):
    help = "Create the standard Zapuza factory role groups"

    def handle(self, *args, **options):
        for role_name in FACTORY_ROLES:
            group, created = Group.objects.get_or_create(
                name=role_name
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created role: {role_name}"
                    )
                )
            else:
                self.stdout.write(
                    f"Role already exists: {role_name}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Factory role groups setup completed."
            )
        )
