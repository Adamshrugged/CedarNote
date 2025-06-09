# --- Libraries ---
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

# --- Basic Configs ---
app = FastAPI()
NOTES_DIR = "notes"
os.makedirs(NOTES_DIR, exist_ok=True)

# Templates and static folder
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --------------------- Routes ---------------------
from routers import notes, folders, autosave, root
# Include routers
app.include_router(notes.router)
app.include_router(folders.router)
app.include_router(autosave.router)
app.include_router(root.router)



