from ninja import Schema
from typing import Any


class Success(Schema):
    message: str
    data: Any = None


class Error(Schema):
    error: str