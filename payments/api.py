from datetime import timedelta
from typing import List
from asgiref.sync import sync_to_async

from django.utils import timezone
from django.db.models import F, Sum
from django.template.loader import render_to_string


from ninja import Router
from ninja.responses import codes_4xx

from payments.models import Level, SalaryCycle
from accounts.models import Teacher
from base.schemas import Success, Error
from payments.schemas import LevelCreateSchema, SalaryCycleSchema, LevelSchema, PaymentSlipSchema, BulkCreateCycleSchema
from base.messages import ResponseMessages
from payments.utils import EmailSender


router = Router(tags=['Payments'])


# SALARY CYCLE
# @router.post("/salary-cycle", response={200: SalaryCycleSchema, codes_4xx: Error})
# async def create_salary_cycle(request, payload: SalaryCycleSchema):
#     """ create a salary cycle"""
#     if await SalaryCycle.active_objects.filter(start_date=payload.start_date, end_date=payload.end_date).aexists():
#         return 400, {"error": "Salary Cycle already exists"}
#     salary_cycle = await SalaryCycle.objects.acreate(**payload.dict())
#     return salary_cycle


@router.post("/salary-cycle/bulk-create", response={200: List[SalaryCycleSchema], codes_4xx: Error})
async def create_bulk_salary_cycle(request, payload: BulkCreateCycleSchema):
    if await SalaryCycle.active_objects.filter(start_date=payload.start_date).aexists():
        return 400, {"error": "Salary Cycle already exists"}

    start_date = payload.start_date
    salary_cycles = []
    for _ in range(payload.number_of_cycle):
        end_date = start_date + timedelta(days=payload.days_in_cycle - 1)
        salary_cycle =await SalaryCycle.objects.acreate(start_date=start_date, end_date=end_date, average_work_hour=payload.average_work_hour)
        start_date = end_date
        salary_cycles.append(salary_cycle)
    # print(salary_cycles)
    return salary_cycles


@router.get("/salary-cycle/{id}", response={200: SalaryCycleSchema, codes_4xx: Error})
async def get_salary_cycle(request, id: int):
    """ get a single salary-cycle"""
    salary_cycle = await SalaryCycle.active_objects.filter(pk=id).afirst()
    if not salary_cycle:
        return 400, {"error": ResponseMessages.SALARY_CYCLE_NOT_FOUND}
    return salary_cycle


@router.get("/salary-cycle", response={200: List[SalaryCycleSchema], codes_4xx: Error})
async def get_all_salary_cycle(request):
    """ get all salary cycle. turn to list to get all object asynchoronously"""
    return await sync_to_async(list)(SalaryCycle.active_objects.all())


@router.patch("/salary-cycle/{id}/update", response={200: SalaryCycleSchema, codes_4xx: Error})
async def update_salary_cycle(request, id: int, data: SalaryCycleSchema):
    """ update salary cycle"""
    salary_cycle = await SalaryCycle.active_objects.filter(pk=id).afirst()
    if not salary_cycle:
        return 400, {"error": ResponseMessages.SALARY_CYCLE_NOT_FOUND}
    payload = data.dict(exclude_unset=True)

    field_names = []
    for field_name, value in payload.items():
        setattr(salary_cycle, field_name, value)
        field_names.append(field_name)

    await salary_cycle.asave(update_fields=field_names)
    return salary_cycle


@router.delete("/salary-cycle/{id}", response={200: Success, codes_4xx: Error})
async def delete_salary_cycle(request, id: int):
    salary_cycle = await SalaryCycle.active_objects.filter(pk=id).afirst()
    if not salary_cycle:
        return 400, {"error": ResponseMessages.SALARY_CYCLE_NOT_FOUND}

    await salary_cycle.adelete()
    return 200, {"message": "Salary cycle deleted successfully"}


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
def generate_payment_slip(request):
    """ get total work hour of the current salary cycle of teachers """
    current_date = timezone.now().date()

    current_salary_cycle = SalaryCycle.active_objects.filter(
        start_date__lte=current_date, end_date__gte=current_date).first()

    if current_date != current_salary_cycle.end_date:
        return 400, {"error": f"Payment slip cannot be generated til {current_salary_cycle.end_date}."}
    
    # get teacher total work hour and total pay within a salary cycle if there attendance clock-out is not null
    qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False,
                                       attendance__date__range=(
                                           current_salary_cycle.start_date, current_salary_cycle.end_date)
                                       ).values("email", "account_number"
                                                ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
                                                                                )).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade')))
    # print(qs)
    return qs

@router.get("/teacher-slip", response={200:Success})
def send_teacher_pay_slip(request):
    #send teacher pay slip if today is salary cycle end date
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
