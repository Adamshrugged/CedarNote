from fastapi import Request
from starlette.responses import RedirectResponse
import json
from core.config import USERS_FILE, AUTH_REQUIRED


# Can either be a basic or strong auth system based on config file
def require_login(request: Request):
    if not AUTH_REQUIRED:
        # This means "use the new auth system" (e.g., OAuth) — placeholder for now
        # For now we'll assume the OAuth system sets the session username already
        user = get_current_user(request)
        if not user:
            # New auth will have its own login flow (e.g. /auth/google)
            return RedirectResponse("/auth/login", status_code=303)
        return user

    # Current basic auth system
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user



def get_current_user(request: Request):
    return request.session.get("username")

def is_superuser(username: str) -> bool:
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    return users.get(username, {}).get("is_superuser", False)


def get_all_users():
    with open(USERS_FILE) as f:
        return list(json.load(f).keys())  # assuming top-level keys are usernames
