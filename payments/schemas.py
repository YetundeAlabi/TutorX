from datetime import date
from decimal import Decimal
from pydantic import Field

from ninja import Schema, ModelSchema

from payments.models import SalaryCycle, Level


class SalaryCycleSchema(ModelSchema):
    start_date : date
    end_date: date
    average_work_hour: int


    class Meta:
        model = SalaryCycle
        fields = ["id", "start_date", "end_date", "average_work_hour"]


class LevelCreateSchema(Schema):
    name: str
    pay_grade: int


class LevelSchema(ModelSchema):
    class Meta:
        model = Level
        fields = ["id", "name", "pay_grade"]


class PaymentSlipSchema(Schema):
    email: str
    account_number: str
    total_work_hours: int
    total_pay: float 
    # start_date: date
    # end_date: date