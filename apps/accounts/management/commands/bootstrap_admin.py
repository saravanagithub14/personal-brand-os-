from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the initial Django superuser from environment variables if needed."

    def handle(self, *args, **options):
        User = get_user_model()

        username = self._clean_env("DJANGO_SUPERUSER_USERNAME")
        email = self._clean_env("DJANGO_SUPERUSER_EMAIL")
        password = self._clean_env("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(self.style.WARNING("Skipping admin bootstrap; credentials not fully provided."))
            return

        lookup = {"username": username}
        if User.objects.filter(**lookup).exists():
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' already exists; skipping."))
            return

        create_kwargs = {
            "username": username,
            "email": email or "",
            "password": password,
            "is_staff": True,
            "is_superuser": True,
        }

        # Use the model manager to respect the custom user implementation.
        user = User.objects.create_superuser(**create_kwargs)
        self.stdout.write(self.style.SUCCESS(f"Created superuser '{user.username}'."))

    @staticmethod
    def _clean_env(name):
        import os

        value = os.environ.get(name, "")
        return value.strip()
