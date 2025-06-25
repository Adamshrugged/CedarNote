from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from datetime import datetime
from starlette.responses import RedirectResponse

# --------------------- Helper Functions ---------------------
from utilities.file_ops import list_folders
from utilities.formatting import parse_frontmatter

# Templates and static folder
from core.templates import templates, get_theme, AVAILABLE_THEMES
from core.config import NOTES_DIR
from utilities.users import get_current_user, require_login, get_all_users
from utilities.file_ops import resolve_safe_path, load_shared, save_shared, get_users_shared_with


router = APIRouter()


# -------------------- SHARED NOTES --------------------

# Getting notes shared between users
@router.get("/shared/{owner}/{path:path}", response_class=HTMLResponse)
async def view_shared_note(request: Request, owner: str, path: str):
    viewer = require_login(request)
    if isinstance(viewer, RedirectResponse):
        return viewer

    shared = load_shared()
    if viewer not in shared.get(owner, {}).get(path, []):
        raise HTTPException(status_code=403, detail="Access denied")

    owner_dir = os.path.join(NOTES_DIR, owner)
    safe_path = resolve_safe_path(owner_dir, path)

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Note not found.")

    content = safe_path.read_text()
    theme = get_theme(request)

    return templates.TemplateResponse("edit_note.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        "username": viewer,
        "title": path,
        "content": content,
        "folders": [],
        "is_owner": False,
        "owner": owner
    })


@router.post("/share-note/{path:path}")
async def share_note(request: Request, path: str, recipient: str = Form(...)):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = os.path.join(NOTES_DIR, username)
    safe_path = resolve_safe_path(user_notes_dir, path)

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Note not found.")

    shared = load_shared()
    shared.setdefault(username, {})
    shared[username].setdefault(path, [])

    if recipient not in shared[username][path]:
        shared[username][path].append(recipient)

    save_shared(shared)

    return RedirectResponse(f"/notes/{path}", status_code=303)

# Ability to edit shared notes
@router.post("/shared-save/{owner}/{path:path}")
async def save_shared_note(request: Request, owner: str, path: str, content: str = Form(...)):
    viewer = require_login(request)
    if isinstance(viewer, RedirectResponse):
        return viewer
    shared = load_shared()

    allowed_users = shared.get(owner, {}).get(path, [])
    if viewer not in allowed_users:
        raise HTTPException(status_code=403, detail="You cannot edit this note")

    owner_notes_dir = os.path.join(NOTES_DIR, owner)
    safe_path = resolve_safe_path(owner_notes_dir, path)

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Note not found")

    safe_path.write_text(content, encoding="utf-8")

    return RedirectResponse(f"/shared/{owner}/{path}", status_code=303)


@router.post("/unshare-note/{path:path}")
async def unshare_note(request: Request, path: str, unshare_with: str = Form(...)):
    owner = require_login(request)
    if isinstance(owner, RedirectResponse):
        return owner

    user_notes_dir = os.path.join(NOTES_DIR, owner)
    safe_path = resolve_safe_path(user_notes_dir, path)
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Note not found.")

    shared = load_shared()
    if path in shared.get(owner, {}):
        try:
            shared[owner][path].remove(unshare_with)
            if not shared[owner][path]:  # Remove entry if no one left
                del shared[owner][path]
            if not shared[owner]:
                del shared[owner]
        except ValueError:
            pass  # not shared with that user

    save_shared(shared)
    return RedirectResponse(f"/notes/{path}", status_code=303)


# -------------------- USERS OWN NOTES --------------------

# Delete a note
@router.post("/delete-note/{path:path}")
async def delete_note(request: Request, path: str):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = os.path.join(NOTES_DIR, username)
    safe_path = resolve_safe_path(user_notes_dir, path)

    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.unlink()
    return RedirectResponse(url="/", status_code=303)


# Create a new note - get to display the form and post to save the data
@router.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username
    today = datetime.today().strftime('%Y-%m-%d')
    user_notes_dir = os.path.join(NOTES_DIR, username)
    folders = list_folders(user_notes_dir)
    theme = get_theme(request)
    return templates.TemplateResponse("new_note.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        "username": username,
        "current_date": today,
        "folders": folders
    })

@router.post("/create-note")
async def create_note(
    request: Request,
    title: str = Form(...),
    folder: str = Form(""),
    content: str = Form(...)
):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    base_dir = Path(NOTES_DIR) / username
    base_dir.mkdir(parents=True, exist_ok=True)

    safe_title = title.strip().replace(" ", "_")
    if not safe_title.endswith(".md"):
        safe_title += ".md"

    folder_path = resolve_safe_path(base_dir, folder.strip()) if folder.strip() else base_dir
    folder_path.mkdir(parents=True, exist_ok=True)

    file_location = folder_path / safe_title
    if file_location.exists():
        raise HTTPException(status_code=400, detail="Note with that title already exists.")

    file_location.write_text(content, encoding="utf-8")

    return RedirectResponse(url="/", status_code=303)

# Edit an existing note
@router.get("/notes/{path:path}", response_class=HTMLResponse)
async def edit_note(request: Request, path: str):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = Path(NOTES_DIR) / username
    safe_path = resolve_safe_path(user_notes_dir, path)

    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    markdown_text = safe_path.read_text(encoding="utf-8")
    folders = list_folders(user_notes_dir)
    theme = get_theme(request)

    # 🔐 Safe way to get the current folder relative to the user’s root
    user_notes_root = user_notes_dir.resolve()
    try:
        parent_folder = safe_path.parent.resolve().relative_to(user_notes_root)
        current_folder = "" if parent_folder == Path(".") else str(parent_folder)
    except ValueError:
        raise HTTPException(status_code=400, detail="Note is outside your directory.")

    shared_users = get_users_shared_with(username, path)
    all_users = get_all_users()
    valid_users = [
        user for user in all_users
        if user != username and user not in shared_users
    ]

    return templates.TemplateResponse("edit_note.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        "username": username,
        "title": path,
        "content": markdown_text,
        "folders": folders,
        "is_owner": True,
        "owner": username,
        "valid_users": valid_users,
        "shared_users": shared_users,
        "current_folder": current_folder
    })




# Save notes
@router.post("/save-note/{path:path}")
async def save_note(request: Request, path: str, content: str = Form(...)):
    username = require_login(request)
    if isinstance(username, RedirectResponse):
        return username

    user_notes_dir = os.path.join(NOTES_DIR, username)
    safe_path = resolve_safe_path(user_notes_dir, path)

    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.write_text(content, encoding="utf-8")

    return RedirectResponse(url="/", status_code=303)
