from django.core.management.base import BaseCommand

from accounts.models import Teacher


class Command(BaseCommand):
    help = "bulk create teachers"

    def handle(self, *args, **kwargs):
        pass