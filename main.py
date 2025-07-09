# --- Libraries ---
import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Routers
from routers.api.v1 import files
from routers.frontend.v1 import my_files, notes_browser, folders, theme_picker

# Load environment variables
load_dotenv()
from core.config import SECRET_KEY

# App init
app = FastAPI()


# Session middleware — must be added first and directly
#app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


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
app.include_router(files.router, prefix="/api/v1")
app.include_router(my_files.router)
app.include_router(folders.router)
app.include_router(notes_browser.router)
app.include_router(theme_picker.router)
