from datetime import datetime
from pydantic import Field
from typing import Optional

from ninja import Schema


class TeacherCreateSchema(Schema):
    first_name: str
    last_name: str
    email: str
    level_id: int
    account_number: Optional[str] 
    bank: Optional[str]
    account_name: Optional[str]


class AttendenceSchema(Schema):
    email: str
