# --- Libraries ---
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# --- Basic Configs ---
from core.templates import templates, get_theme, AVAILABLE_THEMES
from core.config import NOTES_DIR, ACTIVE_THEME, SECRET_KEY
app = FastAPI()
os.makedirs(NOTES_DIR, exist_ok=True)


# Templates and static folder
app.mount("/static", StaticFiles(directory="static"), name="static")
#app.mount("/themes", StaticFiles(directory="templates/themes"), name="themes")
app.mount("/theme-static", StaticFiles(directory="templates/themes"), name="theme_static")


# Session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)



# --------------------- Routes ---------------------
from routers import notes, folders, autosave, root, theme_changer, users
# Include routers
app.include_router(notes.router)
app.include_router(folders.router)
app.include_router(autosave.router)
app.include_router(root.router)
app.include_router(theme_changer.router)
app.include_router(users.router)


