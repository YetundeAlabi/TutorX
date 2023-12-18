from django.contrib import admin

from .models import Admin, Attendance, Teacher, Organisation
# Register your models here.


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("teacher", "date", "clock_in", "clock_out")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "level")


admin.site.register(Admin)
admin.site.register(Organisation)
