import calendar

from typing import List
from asgiref.sync import sync_to_async

from django.utils import timezone
from django.db.models import F, Sum, ExpressionWrapper, fields, Value, Case, When
from django.template.loader import render_to_string
from django.conf import settings

from ninja import Router
from ninja.responses import codes_4xx

from payments.models import Level, Organisation
from accounts.models import Teacher, Attendance
from base.schemas import Success, Error
from payments.schemas import LevelCreateSchema, LevelSchema, PaymentSlipSchema, OrganisationSchema
from base.messages import ResponseMessages
from payments.utils import EmailSender


router = Router(tags=['Payments'])


@router.post("/organisation", response={200: OrganisationSchema, codes_4xx: Error})
async def create_org(request, payload: OrganisationSchema):
    """ create organisation and weekly_work_hours"""
    org = await Organisation.objects.create(**payload.dict())
    return org


@router.get("/organisation/{org_id}", response={200: OrganisationSchema, codes_4xx: Error})
async def create_org_detail(request, org_id: int, payload: OrganisationSchema):
    """ create organisation and weekly_work_hours"""
    org = await Organisation.objects.filter(pk=id).afirst()
    return org


@router.patch("/organisation/{org_id}", response={200: Success, codes_4xx: Error})
async def update_org(request, org_id: int, payload: OrganisationSchema):
    """ create organisation and weekly_work_hours"""
    org = await Organisation.objects.filter(pk=id).afirst()

    data = payload.dict(exclude_unset=True)

    field_names = []
    for field_name, value in data.items():
        setattr(org, field_name, value)
        field_names.append(field_name)

    await org.asave(update_fields=field_names)

    return {"message": "Organisation settings updated successfully"}


# LEVEL
@router.post("/level/create", response={200: LevelSchema})
async def create_level(request, payload: LevelCreateSchema):
    """ create a level"""
    level = await Level.objects.acreate(**payload.dict())
    return level


@router.get("/level/{id}", response={200: LevelSchema, codes_4xx: Error})
async def get_level(request, id: int):
    """ get a single level"""
    level = await Level.active_objects.filter(pk=id).afirst()
    if not level:
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}
    return level


@router.get("/level", response={200: List[LevelSchema], codes_4xx: Error})
async def get_all_level(request):
    """ get all salary cycle"""
    return await sync_to_async(list)(Level.active_objects.all())


@router.patch("/level/{id}/update", response={200: LevelSchema, codes_4xx: Error})
async def update_level(request, id: int, data: LevelSchema):
    """ update salary cycle"""
    level = await Level.active_objects.filter(pk=id).afirst()
    if not level:
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}
    payload = data.dict(exclude_unset=True)

    field_names = []
    for field_name, value in payload.items():
        setattr(level, field_name, value)
        field_names.append(field_name)

    await level.asave(update_fields=field_names)
    return level


@router.delete("/level/{id}", response={200: Success, codes_4xx: Error})
async def delete_level(request, id: int):
    level = await Level.active_objects.filter(pk=id).afirst()
    if not level:
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}

    # level cannot be deleted if teachers are in it
    if await level.teachers.acount() != 0:
        return 400, {"error": "Level cannot be deleted. Teachers are associated with it"}

    await level.adelete()
    return 200, {"message": "Level deleted successfully"}


@router.get("/salary-slip", response={200: List[PaymentSlipSchema], 400: Error}, auth=None)
def generate_payment_slip(request):
    """
      generate slip for teachers at the last day of the month at past 4pm
      total work hours,
      total regular work hours (days present * daily work hours)
      overtime hours


    """
    # pay_day = Settings.active_objects.only("value").filter(name=PAY_DAY).afirst()

    current_datetime = timezone.now()
    current_year = current_datetime.year
    current_month = current_datetime.month
    current_day = current_datetime.day

    # this returns the number of days in the current month
    _, last_date_in_current_month = calendar.monthrange(
        current_year, current_month)

    # check if today date is date of last day of the  month
    if current_day != last_date_in_current_month:
        return 400, {"error": f"Payment slip cannot be generated till {last_date_in_current_month}th of the month."}

    # payment slip is generated after 4:00pm
    if current_datetime <= "4:00pm":
        return 400, {"error": "Payment slip cannot be accessed till after 4:00pm"}

    # get teacher total salary pay
    # get total_work_hour for the month

    daily_work_hours = Organisation.active_objects.only(
        'work_hour_per_day', 'overtime_rate').filter(pk=1)
    # regular_work_hour = settings.AVERAGE_WORK_HOUR

    # clock everyone out at 4:00pm if they've not clock out
    attendance_qs = Attendance.active_objects.filter(
        clock_out_isnull=True, date=current_datetime)
    if attendance_qs.exists:
        clock_out_time = timezone.now().replace(
            hour=16, minute=0, second=0, microsecond=0)
        attendance_qs.update(clock_out=clock_out_time)
    
    qs = Teacher.active_objects.filter(
        attendance__date__month=current_month
    ).values(
        "email", "account_number"
    ).annotate(
        total_regular_work_hours=ExpressionWrapper(
            Sum('attendance', distinct=True) * daily_work_hours,
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

    print(qs)
    return qs


@router.get("/teacher-slip", response={200: Success}, auth=None)
def send_teacher_pay_slip(request):
    # send teacher pay slip if today is pay day
    current_date = timezone.now().date()
    # get teacher total work hour and total pay within a salary cycle if there attendance clock-out is not null
    # qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False,
    #                                    attendance__date__range=(current_salary_cycle.start_date, current_salary_cycle.end_date)
    #                                    ).values("email", "account_number", "first_name", "level__pay_grade"
    #                                     ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
    #                                     )).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade')))
    current_datetime = timezone.now()
    _, current_week, current_day = current_datetime.isocalendar()

    # regular_work_hour = Organisation.objects.only("work_hours").filter(pk=1).first()
    # qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False, attendance__date__week=current_week
    #                                    ).values("email", "account_number"
    #                                             ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'))
    #                                                        ).annotate(overtime_hours=Case(
    #                                                            When(total_work_hours__gt=weekly_work_hours, then=F(
    #                                                                 'total_work_hours') - weekly_work_hours),
    #                                                            default=Value(
    #                                                                0),
    #                                                        )).annotate(regular_work_hours=F('total_work_hours') - F('overtime_hours'),
    #                                                                    regular_work_hours_pay=F(
    #                                                            'regular_work_hours') * F('level__pay_grade'),
    #     over_time_pay=(
    #                                                            F('overtime_hours') * (F('level__pay_grade') * 1.5)),
    #     total_pay=(F('regular_work_hours_pay') + F('over_time_pay')))
    regular_work_hour = settings.AVERAGE_WORK_HOUR
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
                                              "total_regular_work_hours": teacher["total_regular_work_hours"], "overtime_hours": teacher["overtime_hours"],
                                              "pay_per_hour": teacher["level__pay_grade"], "work_hours_pay": teacher["work_hours_pay"],
                                              "overtime_pay": teacher["over_time_pay"], "total_pay": teacher["total_pay"]})

        EmailSender.teacher_payment_mail(teacher["email"], mail_body)
    return {"message": "Email sent"}
