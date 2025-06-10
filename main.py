# --- Libraries ---
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

# --- Basic Configs ---
from core.templates import templates
from core.config import NOTES_DIR, ACTIVE_THEME
app = FastAPI()
os.makedirs(NOTES_DIR, exist_ok=True)



# Templates and static folder
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    f"/theme-static",
    StaticFiles(directory=f"templates/themes/{ACTIVE_THEME}"),
    name="theme_static"
)

print(ACTIVE_THEME)


# --------------------- Routes ---------------------
from routers import notes, folders, autosave, root
# Include routers
app.include_router(notes.router)
app.include_router(folders.router)
app.include_router(autosave.router)
app.include_router(root.router)



