from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Libraries ---
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

# Database and models
from models.db import create_db_and_tables, get_session
from models.user import User
import json

# Routers
from routers.api.v1 import files
from routers.api.v1.auth import google as google_auth
from routers.frontend.v1 import home_page, my_files, notes_browser, folders, theme_picker, admin, friends_ui, share_ui

# Users, friends, sharing
from routers.api.v1 import friends, share, users


# Create tables in database
create_db_and_tables()
is_prod = os.getenv("ENV") == "PRODUCTION"
print(is_prod)
# App init
app = FastAPI(
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json"
)



#
# --- Dev user seeding ---
if not is_prod:
    from sqlmodel import select
    with open("dev_users.json") as f:
        dev_users = json.load(f)

    with get_session() as session:
        for user_data in dev_users:
            user = session.exec(select(User).where(User.email == user_data["email"])).first()
            if not user:
                session.add(User(**user_data))
        session.commit()




# Session middleware — must be added first and directly
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    session_cookie="session",
)


# Theme middleware — depends on session
"""
class ThemeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only try to access session if it's already set up
        try:
            session = request.session
            theme = session.get("user_theme", "default")
        except Exception:
            theme = "default"

        request.state.theme = theme
        print(f"Active theme: {theme}")
        return await call_next(request)"""

#app.add_middleware(ThemeMiddleware)

# Mount static directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/theme-static", StaticFiles(directory="templates/themes"), name="theme_static")



# Routes
app.include_router(google_auth.router)
app.include_router(files.router, prefix="/api/v1")
app.include_router(home_page.router)
app.include_router(my_files.router)
app.include_router(folders.router)
app.include_router(notes_browser.router)
app.include_router(theme_picker.router)

# Sharing
app.include_router(friends.router)
app.include_router(share.router)
app.include_router(users.router)
app.include_router(friends_ui.router)
app.include_router(share_ui.router)

# Admin stuff
app.include_router(admin.router)
