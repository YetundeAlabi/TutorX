from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from base.models import BaseModel
from payments.models import Level
# Create your models here.

User = get_user_model()


class Organisation(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    work_hour_per_day = models.PositiveIntegerField()
    overtime_percent = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and Organisation.objects.exists():
            # if check for self.pk so error will not be raised in the update of exists model
            raise ValidationError(
                'There is can be only one organisation instance')
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Admin(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_user')
    is_admin = models.BooleanField(default=True)


class Teacher(BaseModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=225, unique=True)
    account_number = models.CharField(max_length=10, unique=True)
    account_name = models.CharField(max_length=150, null=True)
    bank = models.CharField(max_length=150, null=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, related_name="teachers")

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class Attendance(BaseModel):
    date = models.DateField()
    clock_in= models.DateTimeField()
    clock_out = models.DateTimeField(null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="attendance")

    def __str__(self):
        return self.teacher.email
    

class PromotionDemotion(BaseModel):
    date = models.DateField(auto_now_add=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    is_promoted = models.BooleanField(default=False)
    is_demoted = models.BooleanField(default=False)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, related_name="promotion_demotion")
    demotion_reason = models.CharField(max_length=255, null=True, blank=True)
