from django.contrib import admin

# Register your models here.
from .models import SalaryCycle, Level

@admin.register(SalaryCycle)
class SalaryCycleModelAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'average_work_hour')


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'pay_grade')