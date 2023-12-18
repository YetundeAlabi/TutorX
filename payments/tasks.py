from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import F, Sum, ExpressionWrapper, fields, Value, Case, When, Count
from django.template.loader import render_to_string

from tutorX.celery import app
from accounts.models import Teacher, Organisation
from payments.utils import EmailSender


@app.task
def send_teacher_pay_slip():
    # send teacher pay slip if today is pay day
    current_datetime = timezone.now()
    if current_datetime.day == 1:

        previous_datetime = current_datetime - relativedelta(months=1)

        previous_month = previous_datetime.month

        org = Organisation.objects.only(
            'work_hour_per_day', 'overtime_percent').filter().first()

        daily_work_hours = org.work_hour_per_day
        overtime_percent = org.overtime_percent

        # generate payslip
        qs = Teacher.active_objects.filter(
            attendance__date__month=previous_month
        ).values(
            "email", "first_name", "level__pay_grade"
        ).annotate(
            total_regular_work_hours=ExpressionWrapper(
                Count('attendance', distinct=True) * daily_work_hours,
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
            ),
            overtime_rate=ExpressionWrapper(F('level__pay_grade') * (overtime_percent / 100) + (
                F('level__pay_grade')), output_field=fields.FloatField())
        ).annotate(
            work_hours_pay=ExpressionWrapper(
                (F('total_work_hours') - F('overtime_hours')) * F('level__pay_grade'),
                output_field=fields.FloatField()
            )
        ).annotate(
            over_time_pay=ExpressionWrapper(
                F('overtime_hours') * F('overtime_rate'), output_field=fields.FloatField())
        ).annotate(
            total_pay=ExpressionWrapper(
                F('work_hours_pay') + F('over_time_pay'),
                output_field=fields.FloatField()
            )
        )
        for teacher in qs:
            mail_body = render_to_string(template_name="emails/payment/teacher_pay_slip.html",
                                        context={"teacher_name": teacher["first_name"], "total_work_hours": teacher["total_work_hours"],
                                                "total_regular_work_hours": teacher["total_regular_work_hours"], "overtime_hours": teacher["overtime_hours"],
                                                "pay_per_hour": teacher["level__pay_grade"], "work_hours_pay": teacher["work_hours_pay"],
                                                "overtime_pay": teacher["over_time_pay"], "total_pay": teacher["total_pay"]})

            EmailSender.teacher_payment_mail(teacher["email"], mail_body)
