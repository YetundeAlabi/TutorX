import csv
from datetime import datetime
from typing import List

from ninja import Router, File
from ninja.files import UploadedFile
from ninja.responses import codes_4xx

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Teacher, Attendance
from accounts.schemas import TeacherSchema, AttendenceSchema, PromotionSchema
from payments.models import Level, SalaryCycle
from base.schemas import Success, Error
from accounts.helpers import get_attendence_async
from base.messages import ResponseMessages

User = get_user_model()
router = Router(tags=['Account'])

# onboard teachers

@router.post("/teachers/create", response={200: Success, codes_4xx: Error})
# is admin permissions
async def onboard_teachers(request, payload: TeacherSchema):
    """ Teachers onboarding by an admin"""
    # check if level exist
    if not await Level.active_objects.filter(id=payload.level_id).aexists():
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}
    
    if await Teacher.objects.filter(account_number=payload.account_number).aexists():
        return 400, {"error": "Account number already exist"}
    
    await Teacher.objects.acreate(**payload.dict())
    return 200, {"message": "Teacher created successfully"}


@router.get("/teachers/{id}", response={200: TeacherSchema, codes_4xx:Error})
async def get_teacher(request, id: int):
    """ get a single teacher obj"""
    teacher = await Teacher.active_objects.filter(pk=id).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}
    return teacher


@router.get("/teachers", response={200: List[TeacherSchema], codes_4xx: Error})
async def get_all_teachers(request):
    return await Teacher.active_objects.all()


@router.patch("/teachers/{id}/update", response={200: TeacherSchema, codes_4xx:Error})
async def update_teachers(request, id: int, data: TeacherSchema):
    """ Update teachers credentials """
    teacher =  await Teacher.active_objects.filter(pk=id).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}
    payload = data.dict(exclude_unset=True)
    if payload.level_id and not await Level.active_objects.filter(id=payload.level_id).aexists():
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}
    
    field_names = []
    async for field_name, value in payload.items():
        setattr(teacher, field_name, value)
        field_names.append(field_name)
    
    await teacher.asave(update_fields=field_names)
    return teacher

@router.delete("/teachers/{id}/delete", response={200: Success, codes_4xx: Error})
async def delete_teacher(request, id: int):
    teacher = await Teacher.active_objects.filter(pk=id).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}
    
    await teacher.adelete()
    return 200, {"message": "Teacher deleted successfully"}


@router.post("/import/teachers")  # move to management command
async def bulk_upload_teachers(request, file: UploadedFile = File(...)):
    if not file.name.endswith('csv'):
        return 400, {"error": ResponseMessages.INVALID_FILE_FORMAT}
    reader = csv.reader(file)
    headers = next(reader, None)
    expected_headers = ["first_name", "last_name", "email",
                        "level_id", "account_number", "bank", "account_name"]
    print(headers)
    if headers != expected_headers:
        return 400, {"error": "Invalid CSV file. Headers do not match. Expected headers: {}'.format(', '.join(expected_headers)"}

    errors = []
    for row in reader:
        # check if level_id exists
        try:
            level = Level.active_objects.get(id=row[3])
        except Level.DoesNotExist:
            # append error
            errors.append(f'Level with {row[3]} does not exist')
            continue
        teachers, _ = Teacher.active_objects.aget_or_create(first_name=row[0], last_name=row[1], email=row[2], level=level,
                                                     account_number=row[4], bank=row[5], account_name=[6])
        return teachers
        # write a management script to create admins


@router.post('/attendance', response={200: Success, codes_4xx: Error})
async def register_attendance(request, payload: AttendenceSchema):
    """ endpoint to take attendance. clock in and clock out  """
    teacher = await Teacher.active_objects.filter(email=payload.email).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}

    # check if today's attendence exists
    dt = timezone.now()
    qs = Attendance.active_objects.filter(teacher=teacher, date=dt.date())
    # attendance = await get_attendence_async(
    #     teacher=teacher, date=dt.date())  # turn to async
    # if not await Attendance.active_objects.filter(teacher=teacher, date=dt.date()).aexists():
    if not await qs.aexists():
        await Attendance.active_objects.acreate(date=dt.date(), teacher=teacher, clock_in=dt)
        return 200, {"message": f"Clock in at {dt.strftime('%H:%M:%S')} successful"}

    # can only clock out atleast one hour after clock in
    # attendance = await Attendance.active_objects.filter(teacher=teacher, date=dt.date()).afirst()
    attendance_obj = await qs.afirst()
    if not dt > attendance_obj.clock_in + timezone.timedelta(hours=1):
        return 400, {"error": ResponseMessages.DUPLICATE_CLOCK_IN}

    if attendance_obj.clock_out is not None:
        return 400, {"error": ResponseMessages.DUPLICATE_CLOCK_OUT}

    #     attendance.clock_out
    await qs.aupdate(clock_out=dt)
    # await Attendance.active_objects.filter(teacher=teacher, date=dt.date(), clock_out__isnull=True).aupdate(clock_out=dt)
    return 200, {"message": f"Clock out at {dt.strftime('%H:%M:%S')} successful"}
   
# promotion and demotion


@router.post('/promotion', response={200: Success, codes_4xx: Error})
async def promote_teacher(request, payload: PromotionSchema):
    teacher = await Teacher.active_objects.filter(email=payload.email).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}
    
    if not Level.active_objects.filter(id=payload.level_id).aexists():
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}
