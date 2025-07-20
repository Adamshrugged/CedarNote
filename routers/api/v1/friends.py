from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from sqlmodel import Session, select  # type: ignore
from utilities.users import get_current_user
from models import db
from models.user import User
from models.friend import FriendRequest

from utilities.api_client import verify_api_key
router = APIRouter(prefix="/api/v1/friends", tags=["Friends"])

@router.post("/accept/{from_email}")
async def accept_friend_request(from_email: str, current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    with Session(db.engine) as session:
        request = session.exec(
            select(FriendRequest).where(
                FriendRequest.from_email == from_email,
                FriendRequest.to_email == current_user.email,
                FriendRequest.status == "pending"
            )
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="No request found.")

        request.status = "accepted"
        session.add(request)
        session.commit()

    return RedirectResponse(
        url="/friends?message=Friend request accepted",
        status_code=303
    )

@router.post("/decline/{from_email}")
async def decline_friend_request(from_email: str, current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    with Session(db.engine) as session:
        request = session.exec(
            select(FriendRequest).where(
                FriendRequest.from_email == from_email,
                FriendRequest.to_email == current_user.email,
                FriendRequest.status == "pending"
            )
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="No request found.")

        request.status = "declined"
        session.add(request)
        session.commit()

    return RedirectResponse(
        url="/friends?message=Friend request declined",
        status_code=303
    )


@router.post("/cancel-request/{to_email}")
async def cancel_friend_request(to_email: str, current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    with Session(db.engine) as session:
        request = session.exec(
            select(FriendRequest).where(
                FriendRequest.from_email == current_user.email,
                FriendRequest.to_email == to_email,
                FriendRequest.status == "pending"
            )
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="No pending friend request found.")

        session.delete(request)
        session.commit()

    return RedirectResponse(
        url="/friends?message=Friend request cancelled",
        status_code=303
    )


@router.post("/request")
async def send_friend_request(
    username: str = Form(...),
    current_user: User = Depends(get_current_user), 
    _: str = Depends(verify_api_key)
):
    """
    Send a friend request to another user.
    """
    if username == current_user.email:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself.")

    with Session(db.engine) as session:
        # Check if user exists
        user_exists = session.exec(select(User).where(User.email == username)).first()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found.")

        # Check for duplicate request (outgoing or incoming)
        existing = session.exec(
            select(FriendRequest).where(
                ((FriendRequest.from_email == current_user.email) & (FriendRequest.to_email == username)) |
                ((FriendRequest.from_email == username) & (FriendRequest.to_email == current_user.email))
            )
        ).first()

        if existing:
            return RedirectResponse(
                url=f"/friends?error=Friend request already exists",
                status_code=HTTP_303_SEE_OTHER
            )

        # Create friend request
        request = FriendRequest(from_email=current_user.email, to_email=username)
        session.add(request)
        session.commit()

    #return JSONResponse(content={"message": f"Friend request sent to {username}."})
    return RedirectResponse(
        url=f"/friends?message=Friend request sent to {username}",
        status_code=HTTP_303_SEE_OTHER
    )


@router.post("/remove/{username}")
async def remove_friend(username: str, current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    """
    Unfriend someone.
    """
    return {"message": f"You are no longer friends with {username}."}

@router.get("/list")
async def list_friends(current_user: User = Depends(get_current_user)):
    """
    List all current friends.
    """
    return {"friends": []}  # TODO: Return actual list

@router.get("/requests")
async def get_friend_requests(current_user: User = Depends(get_current_user), _: str = Depends(verify_api_key)):
    """
    Get incoming and outgoing friend requests.
    """
    # TODO: Query FriendRequest table by current_user
    return {
        "incoming": [],  # Requests sent *to* this user
        "outgoing": []   # Requests *from* this user
    }
