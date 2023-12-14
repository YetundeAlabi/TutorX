from django.db import models
from django.db.models import Q

from base.models import BaseModel
# Create your models here.

class SalaryCycle(BaseModel):
    start_date = models.DateField()
    end_date = models.DateField()
    average_work_hour = models.PositiveIntegerField()

    # def save(self, *args, **kwargs):
    #     """check if a start date and end date is not in an existing salary cycle """
    #     if not SalaryCycle.objects.filter(
    #         Q(start_date__range=[self.start_date, self.end_date]) |
    #         Q(end_date__range=[self.start_date, self.end_date])).exists:
    #         super().save(*args, **kwargs)



class Level(BaseModel):
    name = models.CharField(max_length=50)
    pay_grade = models.DecimalField(decimal_places=2, max_digits=20)
    # order = models.AutoField()


    def __str__(self):
        return self.name
