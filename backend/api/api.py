"""The Django Ninja API. Every endpoint needs a session login unless it sets auth=None.
Service exceptions map to HTTP: PermissionDenied 403, PlanConflict 409, InvalidInput 422."""

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.security import django_auth

from api.auth import router as auth_router
from api.routes import router as customer_router
from plans.services import InvalidInput, PlanConflict

api = NinjaAPI(title="SaverAI", auth=django_auth)
api.add_router("/auth", auth_router)
api.add_router("/", customer_router)


@api.exception_handler(PermissionDenied)
def forbidden(request: HttpRequest, exc: PermissionDenied) -> HttpResponse:
    return api.create_response(request, {"detail": str(exc) or "Forbidden."}, status=403)


@api.exception_handler(PlanConflict)
def conflict(request: HttpRequest, exc: PlanConflict) -> HttpResponse:
    return api.create_response(request, {"detail": str(exc)}, status=409)


@api.exception_handler(InvalidInput)
def invalid_input(request: HttpRequest, exc: InvalidInput) -> HttpResponse:
    return api.create_response(request, {"detail": str(exc)}, status=422)
