"""Login, logout and current user. Roles: `admin` = Django staff user, otherwise `customer`."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.errors import HttpError

router = Router(tags=["auth"])


class LoginIn(Schema):
    username: str
    password: str


class MeOut(Schema):
    username: str
    role: str


def current_user(request: HttpRequest) -> User:
    """Return the logged-in user. Ninja's django_auth has already rejected anonymous requests."""
    user = request.user
    if not isinstance(user, User):
        raise HttpError(401, "Not authenticated.")
    return user


def _me(user: User) -> MeOut:
    return MeOut(username=user.username, role="admin" if user.is_staff else "customer")


@router.get("/csrf", auth=None)
def csrf(request: HttpRequest) -> dict[str, str]:
    """Set the CSRF cookie for the frontend and return the token."""
    return {"csrftoken": get_token(request)}


@router.post("/login", auth=None, response=MeOut)
def login_view(request: HttpRequest, payload: LoginIn) -> MeOut:
    user = authenticate(request, username=payload.username, password=payload.password)
    if not isinstance(user, User):
        raise HttpError(401, "Invalid username or password.")
    login(request, user)
    return _me(user)


@router.post("/logout")
def logout_view(request: HttpRequest) -> dict[str, bool]:
    logout(request)
    return {"ok": True}


@router.get("/me", response=MeOut)
def me(request: HttpRequest) -> MeOut:
    return _me(current_user(request))
