from ninja import Schema

class TokenSchema(Schema):
    access: str
    refresh: str = None

class LoginSchema(Schema):
    email: str
    password : str

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


class PromotionSchema(Schema):
    salary_cycle_id : int
    email : str
    is_promoted: bool = True
    level_id : int


class DemotionSchema(Schema):
    salary_cycle_id : int
    email : str
    is_demoted: bool = True
    level_id : int


   