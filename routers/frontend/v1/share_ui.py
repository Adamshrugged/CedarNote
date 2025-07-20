from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from utilities.users import require_login
from models.user import User

router = APIRouter(tags=["Share UI"])
templates = Jinja2Templates(directory="templates")

@router.get("/shared")
async def view_shared_with_me(request: Request):
    """
    Notes shared with the logged-in user.
    """
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    # TODO: Fetch shared notes via DB or /api/v1/share/incoming
    shared_notes = []

    return templates.TemplateResponse("shared_with_me.html", {
        "request": request,
        "username": username,
        "shared_notes": shared_notes,
    })


@router.get("/shared/outgoing")
async def view_notes_shared_by_me(request: Request):
    """
    Notes the user has shared with others.
    """
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    # TODO: Fetch notes user has shared
    shared_by_me = []

    return templates.TemplateResponse("shared_by_me.html", {
        "request": request,
        "username": username,
        "shared_by_me": shared_by_me,
    })
