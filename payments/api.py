from typing import List
from asgiref.sync import sync_to_async

from django.utils import timezone
from django.db.models import F, Sum, Q

from ninja import Router
from ninja.responses import codes_4xx

from payments.models import Level, SalaryCycle
from accounts.models import Teacher
from base.schemas import Success, Error
from payments.schemas import LevelCreateSchema, SalaryCycleSchema, LevelSchema, PaymentSlipSchema, BulkCreateCycleSchema
from base.messages import ResponseMessages
from accounts.helpers import get_teacher_async, get_salary_cycle


router = Router(tags=['Payments'])


# SALARY CYCLE
@router.post("/salary-cycle", response={200: SalaryCycleSchema, codes_4xx: Error})
async def create_salary_cycle(request, payload: SalaryCycleSchema):
    """ create a salary cycle"""
    print("hello")
    print(payload)
    if await SalaryCycle.active_objects.filter(start_date=payload.start_date, end_date=payload.end_date).aexists():
        return 400, {"error": "Salary Cycle already exists"}
    
    # if await get_salary_cycle(Q(start_date__range=[payload.start_date, payload.end_date]) |
    #                           Q(end_date__range=[payload.start_date, payload.end_date])).aexists:
        # return 400, {"error": "Salary Cycle already exists"}
    salary_cycle = await SalaryCycle.objects.acreate(**payload.dict())
    return salary_cycle


@router.post("/bulk-salary-cycle", )
def create_bulk_salary_cycle(request, payload: BulkCreateCycleSchema):
    cycle_days = payload.cycle_days
    average_work_hour = payload.average_work_hour

    for i in range(payload.number):
        SalaryCycle.objects.acreate(start_date=payload.start_date, end_date=set)


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
    async for field_name, value in payload.items():
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
    async for field_name, value in payload.items():
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

    qs = Teacher.active_objects.filter(attendance__clock_out__isnull=False,
                                       attendance__date__range=(
                                           current_salary_cycle.start_date, current_salary_cycle.end_date)
                                       ).values("email", "account_number"
                                                ).annotate(total_work_hours=Sum(F('attendance__clock_out__hour') - F('attendance__clock_in__hour'),
                                                                                )).annotate(total_pay=(F('total_work_hours') * F('level__pay_grade'))).values()
    # print(qs)
    return qs
