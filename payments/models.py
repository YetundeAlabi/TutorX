from django.db import models

from base.models import BaseModel
# Create your models here.


class Level(BaseModel):
    name = models.CharField(max_length=50)
    pay_grade = models.DecimalField(decimal_places=2, max_digits=20)

    def __str__(self):
        return self.name
