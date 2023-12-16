from django.db import models
from django.db.models import Q
from pydantic import ValidationError

from base.models import BaseModel
# Create your models here.

class Organisation(BaseModel):
    name = models.Charfied(max_length=150, unique=True)
    work_hour_per_day = models.PositiveIntegerField()
    working_days = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and Organisation.objects.exists():
            # if you'll not check for self.pk
            # then error will also be raised in the update of exists model
            raise ValidationError(
                'There is can be only one organisation instance')
        return super().save(*args, **kwargs)


class Level(BaseModel):
    name = models.CharField(max_length=50)
    pay_grade = models.DecimalField(decimal_places=2, max_digits=20)
    # order = models.AutoField()


    def __str__(self):
        return self.name
