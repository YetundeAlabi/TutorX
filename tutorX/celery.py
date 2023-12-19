import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorX.settings')

app = Celery('tutorX')

# Configure Celery using settings from Django settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# send teacher salary pay slip at 9.00am on the first_day_of the month
app.conf.beat_schedule = {
    "send_payment_slip_for_teacher_on_the_first_day_of_the_month": {
        "task": 'payments.tasks.send_teacher_pay_slip',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),
    }}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
