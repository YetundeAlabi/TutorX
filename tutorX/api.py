import http
import traceback

from django.conf import settings

from ninja import NinjaAPI
from ninja.errors import AuthenticationError

from accounts.api import router as accounts_router
from payments.api import router as payments_router
from tutorX.parsers import ORJSONParser
from tutorX.renderers import ORJSONRenderer
from accounts.auth import async_auth_bearer
from accounts.exceptions import ExpiredTokenError, EmptyAuthorizationHeader, InvalidToken


api = NinjaAPI(
    title="Tutor X",
    description="Tutor X API",
    parser=ORJSONParser(),
    renderer=ORJSONRenderer(),
    urls_namespace="TutorX",
    auth=async_auth_bearer
)
api.add_router('accounts/', accounts_router)
api.add_router('payments/', payments_router)


def exception_handler_base(request, exc, msg=None, status=http.HTTPStatus.INTERNAL_SERVER_ERROR):
    return api.create_response(
        request,
        {"message": "An error has occurred",
         'error': msg if msg else traceback.format_exc() if settings.DEBUG else "Please contact admin"},
        status=status,
    )


@api.exception_handler(InvalidToken)
def on_invalid_token(request, exc):
    return exception_handler_base(request, exc, msg="Username or password is incorrect. Please try again", status=401)


@api.exception_handler(EmptyAuthorizationHeader)
def on_invalid_token(request, exc):
    return exception_handler_base(request, exc, msg="Authorization token is missing", status=401)


@api.exception_handler(AuthenticationError)
def unauthenticated_exception_handler(request, exc):
    return exception_handler_base(request, exc, msg="Unauthenticated", status=http.HTTPStatus.UNAUTHORIZED)


@api.exception_handler(ExpiredTokenError)
def expired_token_exception_handler(request, exc):
    return exception_handler_base(request, exc, "Session has expired. Please log in again", status=401)


@api.exception_handler(Exception)
def exception_handler(request, exc):
    return exception_handler_base(request, exc)
