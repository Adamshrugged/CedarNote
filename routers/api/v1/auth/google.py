from fastapi import APIRouter, Request, Form
from starlette.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from sqlmodel import select
import os, httpx

from models.db import get_session
from models.user import User

# For dev or local users
import json
with open("dev_users.json", "r") as f:
    USERS = {user["email"]: user for user in json.load(f)}
is_prod = os.getenv("ENV") == "PRODUCTION"

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

# ONLY NEEDED FOR DEV ENVIRONMENT
@router.post("/auth/login")
async def login_user(request: Request, email: str = Form(...)):
    user = USERS.get(email)
    if not user:
        return HTMLResponse("<h3>Unauthorized user</h3>", status_code=401)
    
    # Simulate Google-style session
    request.session["user"] = user
    return RedirectResponse("/", status_code=302)

# ONLY NEEDED FOR DEV ENVIRONMENT
@router.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@router.get("/auth/login", response_class=HTMLResponse)
async def login(request: Request):
    if not is_prod:
        # Dev mode: simple form
        return HTMLResponse("""
            <h2>Dev Login</h2>
            <form method="post" action="/auth/login">
                <input type="email" name="email" placeholder="Email" required>
                <button type="submit">Login</button>
            </form>
        """)
    
    # Production: start Google OAuth
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri) # type: ignore


@router.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)  # type: ignore

    # Get userinfo from Google
    #userinfo_resp = await oauth.google.get("userinfo", token=token)
    userinfo_resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)  # type: ignore
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
