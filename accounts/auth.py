import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, DecodeError
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model


from accounts.models import User
from accounts.exceptions import InvalidToken, ExpiredTokenError, EmptyAuthorizationHeader
from base.constants import (
    ACCESS_TOKEN_LIFETIME,
    HASH_ALG,
    ISSUER,
    SIGNING_KEY,
    AUTH_HEADER,
    AUTH_SCHEME,
)


User = get_user_model()


async def async_auth_bearer(request):
    token = get_auth_header(request)
    return await TokenAuthentication(request, token).authenticate()


class TokenAuthentication:
    def __init__(self, request, token):
        self.request = request
        self.token = token


    async def authenticate(self):
        email = self._get_user_email_from_token()

        user = await get_user(email)

        if not user:
            raise InvalidToken

        return user

    def _get_user_email_from_token(self):
        payload = JWTAuth().decode_token(self.token)
        if not payload.get("user"):
            raise InvalidToken

        return payload["user"].get("email")


def get_auth_header(request):
    headers = request.headers
    auth_value = headers.get(AUTH_HEADER)
    if not auth_value:
        return None
    parts = auth_value.split(" ")

    if parts[0].lower() != AUTH_SCHEME:
        return None
    token = " ".join(parts[1:])
    return token


async def get_user(email):
    return await User.objects.filter(username=email).afirst()


class JWTAuth:
    def __init__(self, user=None) -> None:
        self.user = user

    def get_payload(self):
        if not self.user:
            raise Exception("User not provided")

        return {
            "iss": settings.JWT[ISSUER],
            "iat": timezone.now(),
            "exp": timezone.now() + settings.JWT[ACCESS_TOKEN_LIFETIME],
            "user": {
                "email": self.user.username,
            },
        }

    def generate_access_token(self):
        access = jwt.encode(
            self.get_payload(),
            settings.JWT[SIGNING_KEY],
            algorithm=HASH_ALG,
        )
        return access

    def generate_token_pair(self):
        payload = self.get_payload()
        payload["ref"] = True

        refresh = jwt.encode(
            payload,
            settings.JWT[SIGNING_KEY],
            algorithm=HASH_ALG,

        )
        return self.generate_access_token(), refresh

    def decode_token(self, encoded: str):
        try:
            payload = jwt.decode(
                encoded, settings.JWT[SIGNING_KEY], algorithms=HASH_ALG)
        except (ExpiredSignatureError, InvalidSignatureError):
            raise ExpiredTokenError
        except DecodeError:
            raise EmptyAuthorizationHeader
        else:
            return payload

    def decode_refresh_token(self, encoded: str):
        try:
            payload = jwt.decode(
                encoded, settings.JWT[SIGNING_KEY], algorithms=HASH_ALG, leeway=timedelta(minutes=30))
        except (ExpiredSignatureError, InvalidSignatureError):
            raise ExpiredTokenError
        except DecodeError:
            raise EmptyAuthorizationHeader
        else:
            return payload
