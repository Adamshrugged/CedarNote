from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os


router = APIRouter()

oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


# --------------------- Routes ---------------------
@router.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        print("Token:", token)
        #user = await oauth.google.parse_id_token(request, token)
        user = token["userinfo"]
        if not user:
            user = await oauth.google.parse_id_token(request, token)
        print("User:", user)
        request.session["username"] = user["email"]
        return RedirectResponse(url="/")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return RedirectResponse(url="/error")  # or show an error page

