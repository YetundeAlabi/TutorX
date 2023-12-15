from asgiref.sync import sync_to_async

from .models import Attendance, Teacher
from payments.models import SalaryCycle

def get_attendence(**kwargs):
    return Attendance.active_objects.filter(**kwargs)

get_attendence_async = sync_to_async(get_attendence)

def get_teacher(**kwargs):
    return Teacher.active_objects.filter(**kwargs)

get_teacher_async = sync_to_async(get_teacher)


def get_salary_cycle(**kwargs):
    return SalaryCycle.active_objects.filter(**kwargs)


get_salary_cycle_async = sync_to_async(get_salary_cycle)
