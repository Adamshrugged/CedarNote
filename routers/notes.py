from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
import os
import pathlib
from datetime import datetime
from starlette.responses import RedirectResponse

# --------------------- Helper Functions ---------------------
from utilities.file_ops import list_folders
from utilities.formatting import parse_frontmatter

# Templates and static folder
from core.templates import templates, get_theme, get_templates, AVAILABLE_THEMES
from core.config import NOTES_DIR


router = APIRouter()


# Delete a note
@router.post("/delete-note/{path:path}")
async def delete_note(path: str):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.unlink()  # Delete the file

    return RedirectResponse(url="/", status_code=303)

# Create a new note - get to display the form and post to save the data
@router.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    today = datetime.today().strftime('%Y-%m-%d')
    folders = list_folders(NOTES_DIR)
    theme = get_theme(request)
    return templates.TemplateResponse("new_note.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
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

    return RedirectResponse(url="/", status_code=303)

# Convert Markdown to HTML
@router.get("/notes/{path:path}", response_class=HTMLResponse)
async def edit_note(request: Request, path: str):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    markdown_text = safe_path.read_text(encoding="utf-8")
    folders = list_folders(NOTES_DIR)
    theme = get_theme(request)

    lines = markdown_text.split("\n")
    better_title = ""
    if lines[0].strip() == "---":
        print("yes")
        better_title = lines[1][8:][:-1]

    return templates.TemplateResponse("edit_note.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        "title": path,
        "better_title": better_title,
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

    return RedirectResponse(url="/", status_code=303)