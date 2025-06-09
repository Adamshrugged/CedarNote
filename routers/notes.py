from fastapi import APIRouter, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import pathlib
from datetime import datetime

# --------------------- Helper Functions ---------------------
from utilities.file_ops import list_folders
from utilities.formatting import parse_frontmatter
from utilities.build_folder_tree import build_folder_tree


NOTES_DIR = "notes"
os.makedirs(NOTES_DIR, exist_ok=True)

# Templates and static folder
templates = Jinja2Templates(directory="templates")


router = APIRouter()


# Delete a note
@router.post("/delete-note/{path:path}")
async def delete_note(path: str):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.unlink()  # Delete the file

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)

# Create a new note - get to display the form and post to save the data
@router.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    today = datetime.today().strftime('%Y-%m-%d')
    folders = list_folders(NOTES_DIR)
    return templates.TemplateResponse("new_note.html", {
        "request": request,
        "current_date": today,
        "folders": folders
    })
@router.post("/create-note")
async def create_note(title: str = Form(...), folder: str = Form(""), content: str = Form(...)):
    safe_title = title.replace(" ", "_")
    if not safe_title.endswith(".md"):
        safe_title += ".md"

    if folder:
        folder_path = os.path.join(NOTES_DIR, folder.strip())
    else:
        folder_path = NOTES_DIR

    file_location = os.path.join(folder_path, safe_title)

    # Prevent overwriting existing notes
    if os.path.exists(file_location):
        raise HTTPException(status_code=400, detail="Note with that title already exists.")

    os.makedirs(folder_path, exist_ok=True)  # Ensure folder exists

    with open(file_location, "w", encoding="utf-8") as f:
        f.write(content)

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)

# Convert Markdown to HTML
@router.get("/notes/{path:path}", response_class=HTMLResponse)
async def edit_note(request: Request, path: str):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    markdown_text = safe_path.read_text(encoding="utf-8")
    folders = list_folders(NOTES_DIR)

    return templates.TemplateResponse("edit_note.html", {
        "request": request,
        "title": path,
        "content": markdown_text,
        "folders": folders
    })

# Save existing notes back to file
@router.post("/save-note/{path:path}")
async def save_note(path: str, content: str = Form(...)):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.write_text(content, encoding="utf-8")

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)