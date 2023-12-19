from pydantic import validator

from ninja import Schema


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
    
    @validator('total_work_hours', 'work_hours_pay', 'over_time_pay', 'total_pay', pre=True, always=True)
    def round_float_values(cls, value):
        # Round the float value to 2 decimal places
        return round(value, 2)
