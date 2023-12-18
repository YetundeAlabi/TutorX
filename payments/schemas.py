from ninja import Schema
from decimal import Decimal


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
    total_regular_work_hours: int
    total_work_hours: float
    overtime_hours: int
    work_hours_pay: float
    over_time_pay: float
    total_pay: float
    