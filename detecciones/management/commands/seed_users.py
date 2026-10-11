from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to seed initial test users: 'lolo' (admin) and 'pablito' (operator).
    """
    help = 'Seeds initial test users for the waste classification system'

    def handle(self, *args, **options):
        test_users = [
            {
                'username': 'lolo',
                'password': 'admin123',
                'first_name': 'Lolo',
                'email': 'lolo@example.com',
                'phone': '123456789',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'pablito',
                'password': 'admin123',
                'first_name': 'Pablito',
                'email': 'pablito@example.com',
                'phone': '987654321',
                'role': 'operator',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        self.stdout.write("Seeding test users...")

        for user_data in test_users:
            username = user_data['username']
            password = user_data.pop('password')

            user, created = User.objects.get_or_create(
                username=username,
                defaults=user_data
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"User '{username}' created successfully with role '{user.role}'.")
                )
            else:
                for field, value in user_data.items():
                    setattr(user, field, value)
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.WARNING(f"User '{username}' already existed. Credentials and attributes updated.")
                )

        self.stdout.write(self.style.SUCCESS("User seeding finished."))
