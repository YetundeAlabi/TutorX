from datetime import datetime
from ninja import Schema, ModelSchema

from payments.models import SalaryCycle, Level


class SalaryCycleSchema(ModelSchema):
    # start_date : datetime
    # end_date: datetime
    # average_work_hour: int
    class Meta:
        model = SalaryCycle
        fields = ["id", "start_date", "end_date", "average_work_hour"]


class LevelCreateSchema(Schema):
    name: str
    pay_grade: int


class LevelSchema(ModelSchema):
    class Meta:
        model = Level
        fields = ["id", "name", "pay_grade", "order"]
