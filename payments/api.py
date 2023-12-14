from typing import List

from django.utils import timezone
from django.db.models import F, fields

from ninja import Router
from ninja.responses import codes_4xx

from payments.models import Level, SalaryCycle
from accounts.models import Attendance, Teacher
from base.schemas import Success, Error
from payments.schemas import LevelCreateSchema, SalaryCycleSchema, LevelSchema
from base.messages import ResponseMessages


router = Router(tags=['Payment'])

#SALARY CYCLE
@router.post("/salary-cycle")
async def create_salary_cycle(request, payload: SalaryCycleSchema):
    """ create a salary cycle"""
    salary_cycle = await SalaryCycle.objects.acreate(**payload.dict())
    return salary_cycle


@router.get("/salary-cycle/{id}", response={200:SalaryCycleSchema, codes_4xx: Error})
async def get_salary_cycle(request, id: int):
    """ get a single salary-cycle"""
    salary_cycle = await SalaryCycle.active_objects.filter(pk=id).afirst()
    if not salary_cycle:
        return 400, {"error": ResponseMessages.SALARY_CYCLE_NOT_FOUND}
    return salary_cycle


@router.get("/salary-cycle", response={200:List[SalaryCycleSchema], codes_4xx:Error})
async def get_all_salary_cycle(request):
    """ get all salary cycle"""
    return await SalaryCycle.active_objects.all()


@router.patch("/salary-cycle/{id}/update", response={200: SalaryCycle, codes_4xx:Error})
async def update_salary_cycle(request, data: SalaryCycleSchema):
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


#LEVEL
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
    return await Level.active_objects.all()


@router.patch("/level/{id}/update", response={200: LevelSchema, codes_4xx: Error})
async def update_level(request, data: LevelSchema):
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
    
    #level cannot be deleted if teachers are in it
    if await level.teachers.acount() != 0:
        return 400, {"error": "Level cannot be deleted. Teachers are associated with it"}
    
    await level.adelete()
    return 200, {"message": "Level deleted successfully"}




@router.get("/payment")
def generate_payment_slip(request):
    """ get total work hour of the current salary cycle of teachers """
    current_date = timezone.now().date()
    current_salary_cycle = SalaryCycle.objects.filter(start_date__lte=current_date, end_date__gte=current_date).first()
    Attendance.objects.filter(date__range=(current_salary_cycle.start_date, current_salary_cycle.end_date))

    qs = Teacher.objects.annotate(total_work_hours=F('attendance__clock_out') - F('attendance__clock_in')
                                  ).filter(attendance__date__range=(current_salary_cycle.start_date, current_salary_cycle.end_date)
                                ).values_list
