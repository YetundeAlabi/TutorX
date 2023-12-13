from django.db import models
from django.contrib.auth import get_user_model

from base.models import BaseModel
from payments.models import Level
# Create your models here.

User = get_user_model()


class Admin(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_user')
    is_admin = models.BooleanField(default=False)


class Teacher(BaseModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=225, unique=True)
    is_promoted = models.BooleanField(default=False)
    is_demoted = models.BooleanField(default=False)
    account_number = models.CharField(max_length=10, null=True, unique=True)
    account_name = models.CharField(max_length=150, blank=True)
    bank = models.CharField(max_length=150, blank=True)
    level = models.ForeignKey(Level, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.email

        
class Attendance(BaseModel):
    date = models.DateField()
    clock_in= models.DateTimeField()
    clock_out = models.DateTimeField(null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    # status = models.CharField(max_length=8, choices=ATTENDANCE_STATUS, default=ABSENT)
    present = models.BooleanField(default=True) 

    def __str__(self):
        return self.Teacher.email