# --- Libraries ---
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
#from fastapi.staticfiles import StaticFiles
import os

# --- Basic Configs ---
router = APIRouter()
from core.config import NOTES_DIR
from core.templates import templates

# --------------------- Helper Functions ---------------------
#from utilities.file_ops import list_folders
from utilities.formatting import parse_frontmatter
from utilities.build_folder_tree import build_folder_tree


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

    for root, dirs, files in os.walk(NOTES_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, NOTES_DIR)

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

    # Sorting
    if sort == "alphabetical":
        notes.sort(key=lambda x: x["title"].lower(), reverse=(order == "desc"))
    elif sort == "recent":
        notes.sort(key=lambda x: x["modified_time"], reverse=(order == "desc"))

    folder_tree = build_folder_tree(NOTES_DIR)
    
    return templates.TemplateResponse("list_notes.html", {
        "request": request,
        "folder_tree": folder_tree,
        "notes": notes,
        "all_tags": sorted(all_tags),
        "current_sort": sort,
        "current_order": order,
        "current_tag": tag,
        "current_folder": folder  # <-- pass current folder for highlighting
    })