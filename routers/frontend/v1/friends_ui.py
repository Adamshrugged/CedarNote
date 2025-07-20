from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, select # type: ignore
from models.friend import FriendRequest
from models import db

#from utilities.users import require_login
from utilities.users import get_current_user
from utilities.context_helpers import render_with_theme
from models.user import User

router = APIRouter(tags=["Friends UI"])
templates = Jinja2Templates(directory="templates")

@router.get("/friends")
async def view_friends(request: Request):
    """
    Main friends page: show current friends and a form to add new ones.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    
    # Load existing friends and outgoing requests
    with Session(db.engine) as session:
        accepted = session.exec(
            select(FriendRequest).where(
                FriendRequest.status == "accepted",
                ((FriendRequest.from_email == user.email) | (FriendRequest.to_email == user.email))
            )
        ).all()

        outgoing = session.exec(
            select(FriendRequest).where(FriendRequest.from_email == user.email, FriendRequest.status == "pending")
        ).all()

        incoming = session.exec(
            select(FriendRequest).where(
                FriendRequest.to_email == user.email,
                FriendRequest.status == "pending"
            )
        ).all()

    # Normalize into a flat list of the *other* person
    friends = [
        req.to_email if req.from_email == user.email else req.from_email
        for req in accepted
    ]

    # Read flash-style messages
    message = request.query_params.get("message")
    error = request.query_params.get("error")

    return render_with_theme(request, "friends.html", {
        "friends": friends,
        "outgoing_requests": outgoing,
        "incoming_requests": incoming,
        "message": message,
        "error": error
    })


