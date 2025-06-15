# --- Libraries ---
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

# --- Basic Configs ---
from core.templates import templates, get_templates
from core.config import NOTES_DIR, ACTIVE_THEME
app = FastAPI()
os.makedirs(NOTES_DIR, exist_ok=True)


# Templates and static folder
app.mount("/static", StaticFiles(directory="static"), name="static")
#app.mount("/themes", StaticFiles(directory="templates/themes"), name="themes")
app.mount("/theme-static", StaticFiles(directory="templates/themes"), name="theme_static")



# --------------------- Routes ---------------------
from routers import notes, folders, autosave, root, theme_changer
# Include routers
app.include_router(notes.router)
app.include_router(folders.router)
app.include_router(autosave.router)
app.include_router(root.router)
app.include_router(theme_changer.router)



