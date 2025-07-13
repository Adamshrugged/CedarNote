from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth # type: ignore
from sqlmodel import select # type: ignore
import os, httpx # type: ignore

from models.db import get_session
from models.user import User

router = APIRouter()

oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
    userinfo_endpoint='https://www.googleapis.com/oauth2/v3/userinfo'
)


@router.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)

    # Get userinfo from Google
    #userinfo_resp = await oauth.google.get("userinfo", token=token)
    userinfo_resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
    userinfo = userinfo_resp.json()

    email = userinfo["email"]
    name = userinfo.get("name")
    picture = userinfo.get("picture")
    given_name = userinfo.get("given_name")

    # Ensure user exists in DB
    with get_session() as session:
        result = session.exec(select(User).where(User.email == email))
        db_user = result.first()

        if not db_user:
            db_user = User(email=email, name=name, picture=picture)
            session.add(db_user)
            session.commit()
            print(f"✅ Created new user: {email}")
        else:
            print(f"👤 User already exists: {email}")

    # Create folder via internal API
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.get(f"/api/v1/files/{email}/")
        if response.status_code != 200:
            print("⚠️ Failed to create user folder:", response.text)

    # Store in session
    request.session['user'] = {
        "email": email,
        "name": name,
        "picture": picture,
        "given_name": given_name
    }

    return RedirectResponse(url="/my-files")
