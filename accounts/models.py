from django.db import models
from django.contrib.auth import get_user_model

from base.models import BaseModel
from payments.models import Level, SalaryCycle
# Create your models here.

User = get_user_model()


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
    
    # def get_promoted_or_demoted(self, current_salary_cycle):
    #     #change the level of a teacher if they get prompted or demoted in this current cycle
    #     self.promotion_demotion.filter(salary_cycle=current_salary_cycle).level = self.level
    #     self.save(update_fields=['level'])
    
class Attendance(BaseModel):
    date = models.DateField()
    clock_in= models.DateTimeField()
    clock_out = models.DateTimeField(null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="attendance")
    present = models.BooleanField(default=True) 

    def __str__(self):
        return self.teacher.email
    

class PromotionDemotion(BaseModel):
    salary_cycle = models.ForeignKey(SalaryCycle, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    is_promoted = models.BooleanField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, related_name="promotion_level")
    status = models.BooleanField()
