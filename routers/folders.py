import os
from pathlib import Path
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

    user_notes_dir = Path(NOTES_DIR) / username
    folders = list_folders(user_notes_dir)
    theme = get_theme(request)
    return templates.TemplateResponse("new_folder.html", {
        "request": request,
        "available_themes": AVAILABLE_THEMES,
        "theme": theme,
        "username": username,
        "folders": folders
    })


@router.post("/create-folder")
async def create_folder(
    request: Request,
    folder_name: str = Form(...),
    parent_folder: str = Form("")
):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = Path(NOTES_DIR) / username
    safe_folder_name = folder_name.strip().replace(" ", "_")
    if not safe_folder_name:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")

    # Use resolve_safe_path to sanitize parent_folder
    parent_path = resolve_safe_path(user_notes_dir, parent_folder.strip()) if parent_folder.strip() else user_notes_dir
    new_folder_path = parent_path / safe_folder_name

    if new_folder_path.exists():
        raise HTTPException(status_code=400, detail="Folder already exists.")

    new_folder_path.mkdir(parents=True)
    return RedirectResponse(url="/", status_code=303)


@router.post("/move-note")
async def move_note(request: Request, note_path: str = Form(...), destination_folder: str = Form("")):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    base_dir = Path(NOTES_DIR) / username

    source_path = resolve_safe_path(base_dir, note_path)
    if not source_path.exists() or not source_path.is_file():
        raise HTTPException(status_code=404, detail="Note not found")

    if not destination_folder.strip():
        dest_dir = base_dir
    else:
        dest_dir = resolve_safe_path(base_dir, destination_folder.strip())

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Prevent moving into the same directory
    if source_path.parent.resolve() == dest_dir.resolve():
        return RedirectResponse("/", status_code=303)

    dest_path = dest_dir / source_path.name

    # Avoid overwriting existing files
    counter = 1
    while dest_path.exists():
        dest_path = dest_dir / f"{source_path.stem}_{counter}{source_path.suffix}"
        counter += 1

    source_path.rename(dest_path)

    # Redirect to new location (relative to user's root)
    notes_root = base_dir.resolve()
    relative_path = dest_path.resolve().relative_to(notes_root)
    return RedirectResponse(f"/notes/{relative_path}", status_code=303)



@router.post("/delete-folder")
async def delete_folder(request: Request, folder_path: str = Form(...)):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = Path(NOTES_DIR) / username
    folder_to_delete = resolve_safe_path(user_notes_dir, folder_path.strip())

    if not folder_to_delete.exists() or not folder_to_delete.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    if folder_to_delete.resolve() == user_notes_dir.resolve():
        raise HTTPException(status_code=400, detail="Cannot delete root folder")

    subdirs = [f for f in folder_to_delete.iterdir() if f.is_dir()]
    if subdirs:
        raise HTTPException(status_code=400, detail="Folder contains subfolders and cannot be deleted")

    # Move files up one level, handling name conflicts
    for item in folder_to_delete.iterdir():
        if item.is_file():
            target = folder_to_delete.parent / item.name
            counter = 1
            while target.exists():
                target = folder_to_delete.parent / f"{item.stem}_{counter}{item.suffix}"
                counter += 1
            item.rename(target)

    folder_to_delete.rmdir()
    return RedirectResponse("/", status_code=303)
