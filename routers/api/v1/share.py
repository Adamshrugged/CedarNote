from fastapi import APIRouter, Depends, HTTPException, Form, Header
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from sqlmodel import Session, select  # type: ignore
from utilities.users import get_current_user
from models import db
from models.shared import SharedNote
from models.user import User
from models.friend import FriendRequest

from utilities.api_client import verify_api_key

router = APIRouter(prefix="/api/v1/share", tags=["Sharing"])


# Needed for validating shared notes are checked when saving
@router.get("/resolve/{virtual_path:path}")
async def resolve_shared_note(
    virtual_path: str,
    x_user_email: str = Header(...)
):
    with db.get_session() as session:
        result = session.exec(
            select(SharedNote).where(
                SharedNote.shared_with_email == x_user_email,
                SharedNote.note_path == virtual_path
            )
        ).first()

        if result:
            return {
                "is_shared": True,
                "owner": result.owner_email,
                "path": result.note_path
            }

        return {"is_shared": False}



@router.post("/note/{note_path:path}")
async def share_note_with_user(
    note_path: str,
    target_email: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    with Session(db.engine) as session:
        # Check if already shared
        existing = session.exec(
            select(SharedNote).where(
                SharedNote.owner_email == current_user.email,
                SharedNote.note_path == note_path,
                SharedNote.shared_with_email == target_email
            )
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Already shared")

        new_share = SharedNote(
            owner_email=current_user.email,
            note_path=note_path,
            shared_with_email=target_email
        )
        session.add(new_share)
        session.commit()

    return RedirectResponse(
        f"/notes/{note_path}?message=Shared with {target_email}",
        status_code=303
    )

@router.post("/unshare/{note_path}/{target_email}")
async def unshare_note(note_path: str, target_email: str, current_user: User = Depends(get_current_user)):
    """
    Unshare a note with a specific user.
    """
    with db.get_session() as session:
        result = session.exec(
            select(SharedNote).where(
                SharedNote.note_path == note_path,
                SharedNote.owner_email == current_user.email,
                SharedNote.shared_with_email == target_email
            )
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Shared note entry not found")

        session.delete(result)
        session.commit()

    return RedirectResponse(f"/notes/{note_path}?message=Unshared with {target_email}", status_code=302)