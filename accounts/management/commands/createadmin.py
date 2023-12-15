from getpass import getpass

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import Admin

User = get_user_model()

class Command(BaseCommand):
    help = "create admin user"

    def handle(self, *args, **kwargs):
        username = input("Username: ")
        # email = input("Email: ")
        password = getpass(prompt="Password: ")
        user = User.objects.create_user(username=username, password=password)
        Admin.objects.create(user=user)
        print("! Admin created successfully")
