from datetime import date
from decimal import Decimal
from pydantic import Field 
from typing import ClassVar

from ninja import Schema, ModelSchema

from payments.models import SalaryCycle, Level


class BulkCreateCycleSchema(Schema):
    cycle_days : int
    average_work_hour: int
    number : int
    start_date : date


class SalaryCycleSchema(ModelSchema):
    class Config:
        model = SalaryCycle
        model_fields = ["id", "start_date", "end_date", "average_work_hour"]


class LevelCreateSchema(Schema):
    name: str
    pay_grade: int


class LevelSchema(ModelSchema):
    class Config:
        model = Level
        model_fields = ["id", "name", "pay_grade"]


class PaymentSlipSchema(Schema):
    email: str
    account_number: str
    total_work_hours: int
    total_pay: float
    # start_date: date
    # end_date: date
