from fastapi import Request
from starlette.responses import RedirectResponse

def get_current_user(request: Request):
    return request.session.get("username")

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user
