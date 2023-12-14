from datetime import datetime
from pydantic import Field
from typing import Optional

from ninja import Schema


class TeacherSchema(Schema):
    first_name: str
    last_name: str
    email: str
    level_id: int
    account_number: str = None
    bank: str = None
    account_name: str = None


class AttendenceSchema(Schema):
    email: str


class PromotionDemotionSchema(Schema):
    salary_cycle_id : int
    teacher_id : int
    is_promoted: bool
    level_id : int
    status : bool
   