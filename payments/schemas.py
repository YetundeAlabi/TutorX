from datetime import date
from decimal import Decimal
from pydantic import Field 
from ninja import Schema

class SettingSchema(Schema):
    average_work_hour : int
    pay_day : int = Field(ge=1, le=28)


class LevelCreateSchema(Schema):
    name: str
    pay_grade: float


class LevelSchema(Schema):
    id: int
    name: str
    pay_grade: float
    

class PaymentSlipSchema(Schema):
    email: str
    account_number: str
    total_work_hours: int
    total_pay: float
    