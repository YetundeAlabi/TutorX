from django.utils import timezone
from django.db.models import F, Sum
from django.template.loader import render_to_string

from tutorX.celery import app
from payments.models import SalaryCycle
from accounts.models import Teacher
from payments.utils import EmailSender

@app.task
def send_teacher_pay_slip():
    #send teacher pay slip if today is salary cycle end date
    current_date = timezone.now().date()
    current_salary_cycle = SalaryCycle.active_objects.filter(
        start_date__lte=current_date, end_date__gte=current_date).first()
    if current_salary_cycle and current_salary_cycle.end_date == current_date:
        #get teacher total work hour and total pay within a salary cycle if there attendance clock-out is not null 
        qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False
                                           ).values("email", "account_number"
                                            ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
                                            )).filter(attendance__date__range=(current_salary_cycle.start_date, current_salary_cycle.end_date)
                                            ).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade')))
        for teacher in qs:
            mail_body = render_to_string(template_name="emails/payment/teacher_pay_slip.html",
                                        context={"teacher_name": teacher["first_name"], "total_work_hours": teacher["total_work_hours"],
                                                "overtime_pay": "overtime_pay", "account_number": teacher["account_number"], "total_pay": teacher["total_pay"] })
            
            EmailSender.teacher_payment_mail(teacher["email"], mail_body)
