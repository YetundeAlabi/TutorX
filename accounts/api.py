import csv
from typing import List
from asgiref.sync import sync_to_async

from ninja import Router, File
from ninja.files import UploadedFile
from ninja.responses import codes_4xx

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import PromotionDemotion, Teacher, Attendance
from accounts.schemas import (
    TeacherSchema,
    AttendenceSchema,
    PromotionSchema,
    LoginSchema,
    TokenSchema,
    DemotionSchema
)
from accounts.auth import JWTAuth
from payments.models import Level
from base.schemas import Success, Error
from base.messages import ResponseMessages

User = get_user_model()
router = Router(tags=['Account'])


@router.post("/login", response={200: TokenSchema, codes_4xx: Error}, auth=None)
async def login(request, payload: LoginSchema):
    user = await User.objects.filter(username=payload.email).afirst()
    if not user:
        return 400, {"error": ResponseMessages.WRONG_CREDENTIALS_MSG}

    if not user.check_password(payload.password):
        return 400, {"error": ResponseMessages.WRONG_CREDENTIALS_MSG}

    access, refresh = JWTAuth(user).generate_token_pair()
    return 200, {"access": access, "refresh": refresh}


@router.post("/token/refresh", response={200: TokenSchema, codes_4xx: Error}, auth=None)
def refresh_token(request, token: str):
    """
    refresh access token
    """
    payload = JWTAuth().decode_refresh_token(token)
    if not payload.get("ref") and not payload.get("ref"):
        return 400, {"error": ResponseMessages.INVALID_TOKEN_MSG}

    email = payload["user"]["email"]
    user_obj = User.objects.filter(email=email).first()
    if not user_obj:
        return 400, {"error": ResponseMessages.WRONG_CREDENTIALS_MSG}

    access = JWTAuth(user_obj).generate_access_token()
    return {"access": access}


# onboard teachers
@router.post("/teachers/create", response={200: Success, codes_4xx: Error})
async def onboard_teachers(request, payload: TeacherSchema):
    """ Teachers onboarding by an admin"""
    # check if level exist
    if not await Level.active_objects.filter(id=payload.level_id).aexists():
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}

    if await Teacher.objects.filter(account_number=payload.account_number).aexists():
        return 400, {"error": "Account number already exist"}

    await Teacher.objects.acreate(**payload.dict())
    return 200, {"message": "Teacher created successfully"}


@router.get("/teachers/{id}", response={200: TeacherSchema, codes_4xx: Error})
async def get_teacher(request, id: int):
    """ get a single teacher obj"""
    teacher = await Teacher.active_objects.filter(pk=id).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}
    return teacher


@router.get("/teachers", response={200: List[TeacherSchema], codes_4xx: Error})
async def get_all_teachers(request):
    return await sync_to_async(list)(Teacher.active_objects.all())


@router.patch("/teachers/{id}/update", response={200: TeacherSchema, codes_4xx: Error})
async def update_teachers(request, id: int, data: TeacherSchema):
    """ Update teachers credentials """
    teacher = await Teacher.active_objects.filter(pk=id).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}
    payload = data.dict(exclude_unset=True)
    if payload.level_id and not await Level.active_objects.filter(id=payload.level_id).aexists():
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}

    field_names = []
    for field_name, value in payload.items():
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


@router.post("/import/teachers", response={200: Success, codes_4xx: Error})
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
            level = await Level.active_objects.get(id=row[3])
        except Level.DoesNotExist:
            # append error
            errors.append(f'Level with {row[3]} does not exist')
            continue
        teachers, _ = await Teacher.active_objects.aget_or_create(first_name=row[0], last_name=row[1], email=row[2], level=level,
                                                                  account_number=row[4], bank=row[5], account_name=[6])
        return 200, {"message": "Teacher created successfully"}


@router.post('/attendance', response={200: Success, codes_4xx: Error}, auth=None)
async def register_attendance(request, payload: AttendenceSchema):
    """ endpoint to take attendance. clock in and clock out  """
    teacher = await Teacher.active_objects.filter(email=payload.email).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}

    # check if today's attendence exists
    dt = timezone.now()
    qs = Attendance.active_objects.filter(teacher=teacher, date=dt.date())

    if not await qs.aexists():
        await Attendance.active_objects.acreate(date=dt.date(), teacher=teacher, clock_in=dt)
        return 200, {"message": f"Clock in at {dt.strftime('%H:%M:%S')} successful"}

    # can only clock out atleast one hour after clock in
    attendance_obj = await qs.afirst()
    if not dt > attendance_obj.clock_in + timezone.timedelta(hours=1):
        return 400, {"error": ResponseMessages.DUPLICATE_CLOCK_IN}

    if attendance_obj.clock_out is not None:
        return 400, {"error": ResponseMessages.DUPLICATE_CLOCK_OUT}

    await qs.aupdate(clock_out=dt)
    return 200, {"message": f"Clock out at {dt.strftime('%H:%M:%S')} successful"}


# promotion and demotion

@router.post('/promotion', response={200: Success, codes_4xx: Error}, auth=None)
async def promote_teacher(request, payload: PromotionSchema):
    teacher = await Teacher.active_objects.filter(email=payload.email).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}

    level = await Level.active_objects.filter(id=payload.level_id).afirst()
    if not level:
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}

    # if not await SalaryCycle.active_objects.filter(id=payload.salary_cycle_id).afirst():
    #     return 400, {"error": ResponseMessages.SALARY_CYCLE_NOT_FOUND}

    if payload.level_id == level.id:
        return 400, {"error": ResponseMessages.EXISTING_LEVEL}

    # await PromotionDemotion.objects.acreate(teacher=teacher, level=level, is_promoted=payload.is_promoted, salary_cycle_id=payload.salary_cycle_id)

    teacher.level = level
    await teacher.asave(update_fields=["level"])
    #send an email to notify teacher of promotion and pay grade
    return {"message": f"{teacher.full_name} has been promoted to {level.name}"}


@router.post('/demotion', response={200: Success, codes_4xx: Error})
async def demoted_teacher(request, payload: DemotionSchema):
    teacher = await Teacher.active_objects.filter(email=payload.email).afirst()
    if not teacher:
        return 400, {"error": ResponseMessages.TEACHER_NOT_FOUND}

    level = await Level.active_objects.filter(id=payload.level_id).afirst()
    if not level:
        return 400, {"error": ResponseMessages.LEVEL_NOT_FOUND}

    # if not await SalaryCycle.active_objects.filter(id=payload.salary_cycle_id).afirst():
    #     return 400, {"error": ResponseMessages.SALARY_CYCLE_NOT_FOUND}

    if payload.level_id == level.id:
        return 400, {"error": ResponseMessages.EXISTING_LEVEL}

    # await PromotionDemotion.objects.acreate(teacher=teacher, level=level, is_demoted=payload.is_demoted, salary_cycle_id=payload.salary_cycle_id)

    teacher.level = level
    teacher.save(update_fields=["level"])
    # send an email to notify teacher of demotion and pay grade
    return {"message": f"{teacher.full_name} has been demoted to {level.name}"}
