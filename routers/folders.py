import os
import pathlib
import shutil

from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from core.templates import templates
from core.config import NOTES_DIR
from utilities.file_ops import list_folders

router = APIRouter()

@router.get("/new-folder", response_class=HTMLResponse)
async def new_folder_form(request: Request):
    folders = list_folders(NOTES_DIR)
    return templates.TemplateResponse("new_folder.html", {
        "request": request,
        "folders": folders
    })

@router.post("/create-folder")
async def create_folder(folder_name: str = Form(...), parent_folder: str = Form("")):
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
async def move_note(path: str, destination_folder: str = Form(...)):
    safe_path = pathlib.Path(NOTES_DIR) / path
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="Note not found.")

    destination_folder_path = os.path.join(NOTES_DIR, destination_folder.strip())
    if not os.path.exists(destination_folder_path):
        raise HTTPException(status_code=404, detail="Destination folder not found.")

    filename = os.path.basename(path)
    new_file_path = os.path.join(destination_folder_path, filename)

    shutil.move(str(safe_path), new_file_path)
    return RedirectResponse(url="/", status_code=303)
