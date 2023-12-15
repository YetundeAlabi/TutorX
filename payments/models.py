from django.db import models
from django.db.models import Q

from base.models import BaseModel
# Create your models here.

class Settings(BaseModel):
    name = models.Charfied(max_length=150, unique=True)
    value = models.PositiveIntegerField(null=True, Blank=True)


class Level(BaseModel):
    name = models.CharField(max_length=50)
    pay_grade = models.DecimalField(decimal_places=2, max_digits=20)
    # order = models.AutoField()


    def __str__(self):
        return self.name
