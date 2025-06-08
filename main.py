# --- Libraries ---
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import markdown
import pathlib

# --- Your Config ---
app = FastAPI()
NOTES_DIR = "notes"
os.makedirs(NOTES_DIR, exist_ok=True)

# --- Pydantic Data Model ---
class NoteMetadata(BaseModel):
    filename: str

# Setup static folder location
app.mount("/static", StaticFiles(directory="static"), name="static")


# Setup template folder
templates = Jinja2Templates(directory="templates")


# --- Your API Code ---

# Main page - list of notes
@app.get("/", response_class=HTMLResponse)
async def list_notes(request: Request):
    # List all .md files
    notes = [f for f in os.listdir(NOTES_DIR) if f.endswith(".md")]
    return templates.TemplateResponse("list_notes.html", {
        "request": request,
        "notes": notes
    })

# Create a new note - get to display the form and post to save the data
@app.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    return templates.TemplateResponse("new_note.html", {"request": request})

@app.post("/create-note")
async def create_note(title: str = Form(...), content: str = Form(...)):
    # Sanitize title (basic check, you can make it stricter)
    safe_title = title.replace(" ", "_")
    if not safe_title.endswith(".md"):
        safe_title += ".md"
    
    file_location = os.path.join(NOTES_DIR, safe_title)
    
    # Prevent overwriting existing notes
    if os.path.exists(file_location):
        raise HTTPException(status_code=400, detail="Note with that title already exists.")
    
    # Save content to file
    with open(file_location, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Redirect back to the list (FastAPI doesn't have a redirect shortcut — use starlette)
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)



# Convert Markdown to HTML
@app.get("/notes/{filename}", response_class=HTMLResponse)
async def get_note_html(request: Request, filename: str):
    # Secure path handling
    safe_path = pathlib.Path(NOTES_DIR) / filename
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Read and convert Markdown
    markdown_text = safe_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(markdown_text)
    
    # Render template with Markdown content
    return templates.TemplateResponse("note.html", {
        "request": request,
        "title": filename,
        "content": html_body
    })

