
from typing import Any
from django.core.management import BaseCommand
from payments.models import Settings
from base.constants import PAY_DAY, AVERAGE_WORK_HOUR


class Command(BaseCommand):
    help = " create system settings"

    def handle(self, *args, **kwargs):
        Settings.object.create(name=PAY_DAY)
        Settings.object.create(name=AVERAGE_WORK_HOUR)
        print("Pay Day and Average work hour settings created!!!")