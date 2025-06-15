import os
import pathlib
import shutil

from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from core.templates import templates, get_theme, AVAILABLE_THEMES
from core.config import NOTES_DIR
from utilities.file_ops import list_folders, resolve_safe_path
from utilities.users import get_current_user, require_login

router = APIRouter()

@router.get("/new-folder", response_class=HTMLResponse)
async def new_folder_form(request: Request):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username
    folders = list_folders(NOTES_DIR)
    theme = get_theme(request)
    username = get_current_user(request)
    return templates.TemplateResponse("new_folder.html", {
        "request": request,
        "available_themes": AVAILABLE_THEMES,
        "theme": theme,
        "username": username,
        "folders": folders
    })

@router.post("/create-folder")
async def create_folder(request: Request, folder_name: str = Form(...), parent_folder: str = Form("")):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username
    safe_folder_name = folder_name.strip().replace(" ", "_")
    if parent_folder:
        new_folder_path = os.path.join(NOTES_DIR, parent_folder.strip(), safe_folder_name)
    else:
        new_folder_path = os.path.join(NOTES_DIR, safe_folder_name)

    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)
    else:
        raise HTTPException(status_code=400, detail="Folder already exists.")

    return RedirectResponse(url="/", status_code=303)

@router.post("/move-note/{path:path}")
async def move_note(request: Request, path: str, destination_folder: str = Form(...)):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = os.path.join(NOTES_DIR, username)
    source_path = resolve_safe_path(user_notes_dir, path)

    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Note not found")

    dest_dir = resolve_safe_path(user_notes_dir, destination_folder)
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = dest_dir / source_path.name
    source_path.rename(dest_path)

    return RedirectResponse(f"/notes/{destination_folder}/{source_path.name}", status_code=303)

