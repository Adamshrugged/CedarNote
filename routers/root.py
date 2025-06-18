# --- Libraries ---
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
#from fastapi.staticfiles import StaticFiles
import os

# --- Basic Configs ---
router = APIRouter()
from core.config import NOTES_DIR
from core.templates import templates, get_theme, AVAILABLE_THEMES

# --------------------- Helper Functions ---------------------
from utilities.file_ops import get_notes_shared_with
from utilities.formatting import parse_frontmatter
from utilities.build_folder_tree import build_folder_tree
from utilities.users import get_current_user



# --------------------- Paths ---------------------

# Main page - list of notes
@router.get("/", response_class=HTMLResponse)
async def list_notes(
    request: Request,
    sort: str = Query("alphabetical"),
    order: str = Query("asc"),
    tag: str = Query(None),
    folder: str = Query(None)  # <-- NEW
):
    notes = []
    all_tags = set()
    theme = get_theme(request)
    username = get_current_user(request)

    # Redirect to register page if no user session
    if not username:
        return RedirectResponse("/register", status_code=302)



    print("Session:", request.session)
    print("Username:", username)

    user_notes_dir = os.path.join(NOTES_DIR, username)

    # Get the user's notes
    for root, dirs, files in os.walk(user_notes_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, user_notes_dir)

                frontmatter = parse_frontmatter(file_path)

                title = frontmatter.get("title")
                tags = frontmatter.get("tags", [])
                category = frontmatter.get("category", "Uncategorized")
                modified_time = os.path.getmtime(file_path)

                if not title:
                    with open(file_path, "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("#"):
                            title = first_line.lstrip("#").strip()
                        else:
                            title = first_line or file

                note_info = {
                    "filename": relative_path,  # important: relative path with folders
                    "title": title,
                    "tags": tags,
                    "category": category,
                    "modified_time": modified_time,
                }

                # Filter by tag if needed
                if tag and tag not in tags:
                    continue

                # Filter by folder if needed
                if folder:
                    if not relative_path.startswith(folder):
                        continue

                notes.append(note_info)

                for t in tags:
                    all_tags.add(t)

    # Get notes shared with the users
    # Shared notes
    shared_notes_raw = get_notes_shared_with(username)
    shared_notes = []
    for owner, note_path in shared_notes_raw:
        filename = os.path.basename(note_path)
        display_title = f"{filename.replace('_', ' ').replace('.md', '')} [{owner}]"
        shared_notes.append({
            "owner": owner,
            "path": note_path,
            "display_title": display_title
        })


    # Sorting
    if sort == "alphabetical":
        notes.sort(key=lambda x: x["title"].lower(), reverse=(order == "desc"))
    elif sort == "recent":
        notes.sort(key=lambda x: x["modified_time"], reverse=(order == "desc"))

    folder_tree = build_folder_tree(user_notes_dir)
    
    return templates.TemplateResponse("list_notes.html", {
        "request": request,
        "username": username,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        "folder_tree": folder_tree,
        "notes": notes,
        "shared_notes": shared_notes,
        "all_tags": sorted(all_tags),
        "current_sort": sort,
        "current_order": order,
        "current_tag": tag,
        "current_folder": folder
    })