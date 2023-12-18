from typing import List
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import F, Sum, ExpressionWrapper, fields, Value, Case, When, Count
from django.db.models.functions import Extract

from ninja import Router
from ninja.responses import codes_4xx

from payments.models import Level
from accounts.models import Teacher, Organisation
from base.schemas import Success, Error
from payments.schemas import LevelCreateSchema, LevelSchema, PaymentSlipSchema
from base.messages import ResponseMessages


router = Router(tags=['Payments'])

# LEVEL
@router.post("/level/create", response={200: LevelSchema})
async def create_level(request, payload: LevelCreateSchema):
    """ create a level"""
    if payload.parent_level:
        parent_level = Level.active_objects.filter(name__iexact= parent_level).afirst()

    if not parent_level:
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}
    
    level = await Level.objects.acreate(name=payload.name, pay_grade=payload.pay_grade, parent_level=parent_level)
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

    await level.asoft_delete()
    return 200, {"message": "Level deleted successfully"}


@router.get("/salary-slip", response={200: List[PaymentSlipSchema], 400: Error})
def generate_payment_slip(request):
    """
      generate slip for teachers at the last day of the month at past 4pm
      total work hours,
      total regular work hours (days present * daily work hours)
      overtime hours,
      work_hours_pay

    """
    current_datetime = timezone.now()
    previous_datetime = current_datetime - relativedelta(months=1)
    previous_month = previous_datetime.month

    org = Organisation.objects.only(
        'work_hour_per_day', 'overtime_percent').filter().first()
    if not org:
        return 400, {"error": "You have not completed your settings."}

    daily_work_hours = org.work_hour_per_day
    overtime_percent = org.overtime_percent

    # generate payslip
    qs = Teacher.active_objects.filter(
        attendance__date__month=previous_month
    ).values(
        "email", "account_number"
    ).annotate(
        total_regular_work_hours=ExpressionWrapper(
            Count('attendance', distinct=True) * daily_work_hours,
            output_field=fields.DurationField()
        )
    ).annotate(
        total_work_duration=Sum(
            F('attendance__clock_out') - F('attendance__clock_in')),
        total_work_hours=ExpressionWrapper(
            Extract('total_work_duration', 'hour') +
            Extract('total_work_duration', 'minute') / 60,
            output_field=fields.FloatField()
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

    # print(qs)
    return qs
