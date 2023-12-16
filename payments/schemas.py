from ninja import Schema


class OrganisationSchema(Schema):
    name: str
    work_hour_per_day : int
    

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
    