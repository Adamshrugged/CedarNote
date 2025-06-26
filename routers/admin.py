from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER
import json
import os

from utilities.users import is_superuser
from core.templates import templates, get_theme, AVAILABLE_THEMES

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/admin")
def admin_panel(request: Request):
    theme = get_theme(request)
    username = request.session.get("username")
    if not username or not is_superuser(username):
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

    with open("core/users.json") as f:
        users = json.load(f)

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "theme": theme,
        "users": users,
        "username": username
    })

@router.post("/admin/delete-user")
def delete_user(request: Request, user_to_delete: str = Form(...)):
    username = request.session.get("username")
    if not username or not is_superuser(username):
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

    with open("core/users.json", "r+") as f:
        users = json.load(f)
        if user_to_delete in users:
            del users[user_to_delete]
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()

    # Optionally delete their notes:
    user_notes = os.path.join("notes", user_to_delete)
    if os.path.exists(user_notes):
        import shutil
        shutil.rmtree(user_notes)

    return RedirectResponse(url="/admin", status_code=HTTP_303_SEE_OTHER)
