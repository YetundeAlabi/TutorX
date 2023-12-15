import calendar

from decimal import Decimal
from datetime import timedelta
from typing import List
from asgiref.sync import sync_to_async

from django.utils import timezone
from django.db.models import F, Sum
from django.template.loader import render_to_string


from ninja import Router
from ninja.responses import codes_4xx

from payments.models import Level, Settings
from accounts.models import Teacher
from base.schemas import Success, Error
from base.constants import PAY_DAY, AVERAGE_WORK_HOUR
from payments.schemas import LevelCreateSchema, OrganisationSchema, LevelSchema, PaymentSlipSchema, SettingSchema
from base.messages import ResponseMessages
from payments.utils import EmailSender


router = Router(tags=['Payments'])


# SALARY CYCLE
@router.post("/settings", response={200: Success, codes_4xx: Error})
async def create_settings(request, payload: SettingSchema):
    """ create an organisation settings"""
    #check if pay_day has already being set
    if Settings.active_objects.filter(name=PAY_DAY, value=payload.pay_day).aexists():
        return 400, {"error": ResponseMessages.DUPLICATE_PAY_DAY}

    Settings.objects.filter(name=PAY_DAY).aupdate(value=payload.pay_day)

    #check if average work hour has been set
    if Settings.active_objects.filter(name=PAY_DAY, value=payload.average_work_hour).aexists():
        return 400, {"error": ResponseMessages.DUPLICATE_AVERAGE_WORK_HOUR}

    Settings.objects.filter(name=AVERAGE_WORK_HOUR).aupdate(value=payload.average_work_hour)
    return {"message": "Settings configured successfully"}


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


@router.get("/salary-slip", response={200: List[PaymentSlipSchema], 400: Error})
def generate_payment_slip(request, name: str):
    """ get total work hour of teachers at pay day"""
    pay_day = Settings.active_objects.only("value").filter(name=PAY_DAY).afirst()
    current_datetime = timezone.now()
    
    if current_datetime.day != pay_day.value:
        return 400, {"error": f"Payment slip cannot be generated til {pay_day.value}th of the current month."}
    
    # get teacher total work hour and total pay within a salary cycle if there attendance clock-out is not null
    #get teacher total salary pay
    #get total_work_hour for the month
    current_year = current_datetime.year
    current_month = current_datetime.month
    _, days_in_current_month = calendar.monthrange(current_year, current_month)

    settings = Settings.active_objects.filter(name=AVERAGE_WORK_HOUR).annotate(total_avg_work_hour=F('value') * Decimal(days_in_current_month))
    
    qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False,
                                       attendance__date__month=current_month
                                       ).values("email", "account_number"
                                                ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
                                                                                )).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade')))
    # print(qs)
    return qs

@router.get("/teacher-slip", response={200:Success})
def send_teacher_pay_slip(request):
    #send teacher pay slip if today is pay day
    current_date = timezone.now().date()
    current_salary_cycle = SalaryCycle.active_objects.filter(
        start_date__lte=current_date, end_date__gte=current_date).first()
    if current_salary_cycle and current_salary_cycle.end_date == current_date:
        print("got here")
        #get teacher total work hour and total pay within a salary cycle if there attendance clock-out is not null 
        qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False,
                                           attendance__date__range=(current_salary_cycle.start_date, current_salary_cycle.end_date)
                                           ).values("email", "account_number", "first_name", "level__pay_grade"
                                            ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
                                            )).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade')))
        for teacher in qs:
            mail_body = render_to_string(template_name="emails/payment/teacher_pay_slip.html",
                                        context={"teacher_name": teacher["first_name"], "total_work_hours": teacher["total_work_hours"],
                                                "pay_per_hour": teacher["level__pay_grade"], "account_number": teacher["account_number"], "total_pay": teacher["total_pay"] })
            
            EmailSender.teacher_payment_mail(teacher["email"], mail_body)
    return {"message": "Email sent"}
