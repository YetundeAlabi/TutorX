from ninja import Schema
from typing import Union


class Success(Schema):
    message: str


class Error(Schema):
    error: Union[str, list]