import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorX.settings')

# Replace 'your_project' with your project's name.
app = Celery('tutorX')

# Configure Celery using settings from Django settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

#send teacher salary pay slip at 9.00am on salary cycle end_date
app.conf.beat_schedule = {
    "send_payment_slip_for_teacher_on_salary_cycle_end_date": {
        "task": 'payments.tasks.send_teacher_pay_slip',
        'schedule': crontab(minute=24, hour=8),
    }}