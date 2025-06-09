# --- Libraries ---
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form, Body, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import markdown
import pathlib
import yaml
from datetime import datetime
import shutil

# --- Your Config ---
app = FastAPI()
NOTES_DIR = "notes"
os.makedirs(NOTES_DIR, exist_ok=True)

# --- Pydantic Data Model ---
class NoteMetadata(BaseModel):
    filename: str
class ContentBody(BaseModel):
    content: str



# Setup static folder location
app.mount("/static", StaticFiles(directory="static"), name="static")


# Setup template folder
templates = Jinja2Templates(directory="templates")


# --- Your API Code ---

# Auto save edits
@app.post("/autosave-note/{path:path}")
async def autosave_note(path: str, body: ContentBody):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.write_text(body.content, encoding="utf-8")

    return JSONResponse(content={"status": "saved"})



# Main page - list of notes
@app.get("/", response_class=HTMLResponse)
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




# Delete a note
@app.post("/delete-note/{path:path}")
async def delete_note(path: str):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.unlink()  # Delete the file

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)




# Create a new note - get to display the form and post to save the data
@app.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    today = datetime.today().strftime('%Y-%m-%d')
    folders = list_folders(NOTES_DIR)
    return templates.TemplateResponse("new_note.html", {
        "request": request,
        "current_date": today,
        "folders": folders
    })


@app.post("/create-note")
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
@app.get("/notes/{path:path}", response_class=HTMLResponse)
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
@app.post("/save-note/{path:path}")
async def save_note(path: str, content: str = Form(...)):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    safe_path.write_text(content, encoding="utf-8")

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)



# Create a new folder
@app.get("/new-folder", response_class=HTMLResponse)
async def new_folder_form(request: Request):
    folders = list_folders(NOTES_DIR)  # Get list of existing folders
    return templates.TemplateResponse("new_folder.html", {
        "request": request,
        "folders": folders  # Pass to template
    })

@app.post("/create-folder")
async def create_folder(
    folder_name: str = Form(...),
    parent_folder: str = Form("")
):
    safe_folder_name = folder_name.strip().replace(" ", "_")

    if parent_folder:
        new_folder_path = os.path.join(NOTES_DIR, parent_folder.strip(), safe_folder_name)
    else:
        new_folder_path = os.path.join(NOTES_DIR, safe_folder_name)

    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)
    else:
        raise HTTPException(status_code=400, detail="Folder already exists.")

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)



# Move note to folder
@app.post("/move-note/{path:path}")
async def move_note(path: str, destination_folder: str = Form(...)):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="Note not found.")

    destination_folder_path = os.path.join(NOTES_DIR, destination_folder.strip())
    if not os.path.exists(destination_folder_path):
        raise HTTPException(status_code=404, detail="Destination folder not found.")

    filename = os.path.basename(path)  # Extract the filename from path
    new_file_path = os.path.join(destination_folder_path, filename)

    shutil.move(str(safe_path), new_file_path)

    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)



# --------------------- Helper functions ---------------------
 
# Shows all sub folders
def build_folder_tree(base_path):
    folder_tree = []

    for root, dirs, files in os.walk(base_path):
        # Show relative path from NOTES_DIR
        relative_root = os.path.relpath(root, base_path)
        if relative_root == ".":
            relative_root = ""  # Root folder

        folder_info = {
            "folder": relative_root,
            "notes": [],
        }

        for file in files:
            if file.endswith(".md"):
                folder_info["notes"].append(file)

        if folder_info["notes"] or relative_root:
            folder_tree.append(folder_info)

    return folder_tree

 
# Checks for YAML formatting and converts to a dictionary 
def parse_frontmatter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if lines[0].strip() == "---":
        frontmatter_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            frontmatter_lines.append(line)
        frontmatter_text = ''.join(frontmatter_lines)
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            frontmatter = {}
    else:
        frontmatter = {}

    return frontmatter

def list_folders(base_path):
    folders = []
    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            rel_path = os.path.relpath(os.path.join(root, d), base_path)
            folders.append(rel_path)
    return sorted(folders)

