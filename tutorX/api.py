from ninja import NinjaAPI

from accounts.api import router as accounts_router
from payments.api import router as payments_router

from .parsers import ORJSONParser
from .renderers import ORJSONRenderer

api = NinjaAPI(
    title="Tutor X",
    description="Tutor X API",
    parser=ORJSONParser(),
    renderer=ORJSONRenderer(),
    urls_namespace="TutorX"
)
api.add_router('accounts/', accounts_router)
api.add_router('payments/', payments_router )
