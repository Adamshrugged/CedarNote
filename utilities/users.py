from fastapi import Request
from starlette.responses import RedirectResponse
import json
from core.config import USERS_FILE

def get_current_user(request: Request):
    return request.session.get("username")

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user

def is_superuser(username: str) -> bool:
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    return users.get(username, {}).get("is_superuser", False)


def get_all_users():
    with open(USERS_FILE) as f:
        return list(json.load(f).keys())  # assuming top-level keys are usernames
