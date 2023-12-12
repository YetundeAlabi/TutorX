from django.db import models
from django.contrib.auth import get_user_model

from base.models import BaseModel
from base.constants import PRESENT, ABSENT
from payments.models import Level
# Create your models here.

User = get_user_model()

ATTENDANCE_STATUS = (
    (PRESENT, PRESENT),
    (ABSENT, ABSENT),
)

class Admin(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_user')
    is_admin = models.BooleanField(default=False)


class Teacher(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    is_promoted = models.BooleanField(default=False)
    is_demoted = models.BooleanField(default=False)
    account_number = models.CharField(max_length=10, null=True)
    account_name = models.CharField(max_length=150, blank=True)
    bank = models.CharField(max_length=150, blank=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL)
 
    
class Attendance(BaseModel):
    clock_in= models.DateTimeField(auto_now_add=True)
    clock_out = models.DateTimeField(auto_now=True)
    Teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=ATTENDANCE_STATUS, default=ABSENT)