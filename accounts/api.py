import csv
from datetime import datetime

from ninja import Router, File
from ninja.files import UploadedFile
from ninja.responses import codes_4xx

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Teacher, Attendance
from accounts.schemas import TeacherSchema, AttendenceInSchema, AttendenceOutSchema
from payments.models import Level
from base.schemas import Success, Error
User = get_user_model()
router = Router(tags=['User management'])

#onboard teachers
@router.post("/teachers/create", response={200: Success, codes_4xx: Error})
#is admin permissions
async def onboard_teachers(request, payload:TeacherSchema):
    """ Teachers onboarding by an admin"""
    #check if level exist
    if not await Level.objects.filter(id=payload.level_id).aexist():
        return 400, {"error": "Level does not exists"}
    await Teacher.objects.acreate(**payload.dict())
    return 200, {"message": "Teacher created successfully"}

@router.post("import/teachers") #move to management command
async def bulk_upload_teachers(request, file: UploadedFile = File(...)):
    if not file.name.endswith('csv'):
        return 400, {"error": "File must be in csv"}
    reader = csv.reader(file)
    headers = next(reader, None)
    expected_headers = ["first_name", "last_name", "email", "level_id", "account_number", "bank", "account_name"]
    print(headers)  
    if headers != expected_headers:
        return 400, {"error": "Invalid CSV file. Headers do not match. Expected headers: {}'.format(', '.join(expected_headers)"}
    
    errors = []
    for row in reader:
        #check if level_id exists
        try: 
            level = Level.objects.get(id=row[3])
        except Level.DoesNotExist:
            #append error
            errors.append(f'Level with {row[3]} does not exist')
            continue
        teachers, _ = Teacher.objects.aget_or_create(first_name=row[0], last_name=row[1], email=row[2], level=level,
                                                      account_number=row[4], bank=row[5], account_name=[6])
        return teachers
            #write a management script to create admins

# endpoint to take attendance
@router.post('/attendence')
async def register_attendence(request, payload: AttendenceInSchema):
    teacher = Teacher.objects.filter(email=payload.email).afirst()
    if not teacher:
        400, {"error": "Teacher does not exists"}

    #check if today's attendence exists
    dt = timezone.now()
    attendence = Attendance.objects.filter(teacher=teacher, date=dt.date())
    if not attendence.aexist():
        Attendance.objects.create(date=dt.date(), teacher=teacher, clock_in=dt)
        return {"message": f"Clock in at {dt.strftime('%H:%M:%S')} successful"}
    
    #can clock out atleast one hour after clock in
    if dt > attendence.clock_in + timezone.timedelta(hours=1):
        attendence.filter(clock_out__isnull=True).update(clock_out=dt)
    return {"message": f"Clock out at {dt.strftime('%H:%M:%S')} successful"}

#promotion and demotion


