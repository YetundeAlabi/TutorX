from django.db import models

from base.models import BaseModel
# Create your models here.

class SalaryCycle(BaseModel):
    start_date = models.DateField()
    end_date = models.DateField()
    average_work_hour = models.PositiveIntegerField()


class Level(BaseModel):
    name = models.CharField(max_length=50)
    pay_grade = models.PositiveIntegerField()
    order = models.AutoField()


    def __str__(self):
        return self.name
