from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Create all 7 demo user accounts for testing'

    def handle(self, *args, **options):
        users_to_create = [
            {'username': 'superadmin', 'password': 'Superadmin1234!', 'role': 'super_admin',
             'email': 'superadmin@erp.local', 'first_name': 'Super', 'last_name': 'Admin'},
            {'username': 'admin_user', 'password': 'Demo1234!', 'role': 'admin',
             'email': 'admin@erp.local', 'first_name': 'Admin', 'last_name': 'User'},
            {'username': 'manager_user', 'password': 'Demo1234!', 'role': 'manager',
             'email': 'manager@erp.local', 'first_name': 'Store', 'last_name': 'Manager'},
            {'username': 'storekeeper_user', 'password': 'Demo1234!', 'role': 'storekeeper',
             'email': 'storekeeper@erp.local', 'first_name': 'Store', 'last_name': 'Keeper'},
            {'username': 'cashier_user', 'password': 'Demo1234!', 'role': 'cashier',
             'email': 'cashier@erp.local', 'first_name': 'Jane', 'last_name': 'Cashier'},
            {'username': 'accountant_user', 'password': 'Demo1234!', 'role': 'accountant',
             'email': 'accountant@erp.local', 'first_name': 'John', 'last_name': 'Accountant'},
            {'username': 'viewer_user', 'password': 'Demo1234!', 'role': 'viewer',
             'email': 'viewer@erp.local', 'first_name': 'View', 'last_name': 'Only'},
        ]

        for data in users_to_create:
            username = data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  Skipping {username} (already exists)')
                continue

            user = User.objects.create_user(
                username=username,
                password=data['password'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data['role'],
                is_active=True,
            )
            if data['role'] == 'super_admin':
                user.is_staff = True
                user.is_superuser = True
                user.save()

            self.stdout.write(self.style.SUCCESS(
                f'  Created {username} ({data["role"]}) — password: {data["password"]}'
            ))

        self.stdout.write(self.style.SUCCESS('\nDemo users created successfully.'))
        self.stdout.write('Login with username/password above at the login screen.')
