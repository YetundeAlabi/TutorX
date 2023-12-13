from ninja import Schema


class Success(Schema):
    message: str


class Error(Schema):
    error: str