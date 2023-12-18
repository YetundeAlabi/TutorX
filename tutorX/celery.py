import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorX.settings')

app = Celery('tutorX')

# Configure Celery using settings from Django settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

#send teacher salary pay slip at 9.00am on salary cycle end_date
app.conf.beat_schedule = {
    "send_payment_slip_for_teacher_on_salary_cycle_end_date": {
        "task": 'payments.tasks.send_teacher_pay_slip',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),
    }}