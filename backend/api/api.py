"""The Django Ninja API. Every endpoint needs a session login unless it sets auth=None."""

from ninja import NinjaAPI
from ninja.security import django_auth

from api.auth import router as auth_router

api = NinjaAPI(title="SaverAI", auth=django_auth)
api.add_router("/auth", auth_router)
