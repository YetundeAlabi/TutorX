from django.utils import timezone
from django.db.models import F, Sum, ExpressionWrapper, fields, Value, Case, When
from django.template.loader import render_to_string
from django.conf import settings

from tutorX.celery import app
from payments.models import Organisation
from accounts.models import Teacher
from payments.utils import EmailSender

@app.task
def send_teacher_pay_slip():
    #send teacher pay slip if today is salary cycle end date
    current_date = timezone.now().date()
    # print(current_date)
    current_salary_cycle = SalaryCycle.active_objects.filter(
        start_date__lte=current_date, end_date__gte=current_date).first()
    if current_salary_cycle and current_salary_cycle.end_date == current_date:
        #get teacher total work hour and total pay within a salary cycle if there attendance clock-out is not null 
        # qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False
        #                                    ).values("email", "account_number", "first_name"
        #                                     ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
        #                                     )).filter(attendance__date__range=(current_salary_cycle.start_date, current_salary_cycle.end_date)
        #   
        #                                   ).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade')))
        regular_work_hour = settings.AVERAGE_WORK_HOUR
        current_datetime = timezone.now()
        current_month = current_datetime.month
        qs = Teacher.active_objects.filter(
            attendance__clock_out__isnull=False,
            attendance__date__month=current_month
        ).values(
            "email", "first_name", "level__pay_grade"
        ).annotate(
            total_regular_work_hours=ExpressionWrapper(
                Sum('attendance', distinct=True) * regular_work_hour,
                output_field=fields.DurationField()
            )
        ).annotate(
            total_work_hours=ExpressionWrapper(
                Sum(F('attendance__clock_out__hour') -
                    F('attendance__clock_in__hour')),
                output_field=fields.DurationField()
            )
        ).annotate(
            overtime_hours=ExpressionWrapper(
                Case(
                    When(total_work_hours__gte=F('total_regular_work_hours'),
                         then=F('total_work_hours') - F('total_regular_work_hours')),
                    default=Value(0),
                    output_field=fields.DurationField()
                ),
                output_field=fields.DurationField()
            )
        ).annotate(
            work_hours_pay=ExpressionWrapper(
                F('total_work_hours') * F('level__pay_grade'),
                output_field=fields.FloatField()
            )
        ).annotate(
            over_time_pay=ExpressionWrapper(
                F('overtime_hours') * F('level__pay_grade'), output_field=fields.FloatField()) * 1.5
        ).annotate(
            total_pay=ExpressionWrapper(
                F('work_hours_pay') + F('over_time_pay'),
                output_field=fields.FloatField()
            )
        )

        for teacher in qs:
            mail_body = render_to_string(template_name="emails/payment/teacher_pay_slip.html",
                                        context={"teacher_name": teacher["first_name"], "total_work_hours": teacher["total_work_hours"],
                                                "pay_per_hour": teacher["level__pay_grade"], "account_number": teacher["account_number"], "total_pay": teacher["total_pay"]})
            
            EmailSender.teacher_payment_mail(teacher["email"], mail_body)
