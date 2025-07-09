from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import httpx # type: ignore

router = APIRouter()
templates = Jinja2Templates(directory="templates")
from utilities.context_helpers import render_with_theme


# Create a new note - get to display the form and post to save the data
@router.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    username = "adam"
    #username = require_login(request)
    #if isinstance(username, RedirectResponse):
    #    return username
    today = datetime.today().strftime('%Y-%m-%d')

    # Fetch folder list from the API
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.get(f"/api/v1/folders/{username}")
        folder_list = response.json() if response.status_code == 200 else []

    return render_with_theme(request, "new_note.html", {
        "username": username,
        "current_date": today,
        "folders": folder_list
    })

# Creating a new note
@router.post("/create-note")
async def create_note_frontend(
    request: Request,
    title: str = Form(...),
    folder: str = Form(""),
    content: str = Form(...)
):
    username = "adam"  # Replace with session value later
    # Sanitize title
    title = title.replace(" ", "_")

    virtual_path = f"{folder}/{title}" if folder else title

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post(
            f"/api/v1/create/{username}",
            data={"title": title, "folder": folder, "content": content}
        )

    if response.status_code != 200:
        return RedirectResponse("/new-note", status_code=302)

    return RedirectResponse(f"/notes/{virtual_path}", status_code=303)

# Saving / updating a note
@router.post("/save-note/{virtual_path:path}")
async def save_note_frontend(request: Request, virtual_path: str, content: str = Form(...)):
    username = "adam"  # Replace with real session/user later

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post(
            f"/api/v1/files/{username}/{virtual_path}",
            data={"content": content}
        )

    if response.status_code != 200:
        return RedirectResponse("/my-files", status_code=302)  # fallback if something went wrong

    return RedirectResponse(f"/notes/{virtual_path}", status_code=303)

# Moving a note
@router.post("/move-note/{username}/{virtual_path:path}")
async def move_note_frontend(
    request: Request,
    username: str,
    virtual_path: str,
    destination_folder: str = Form(...)
):
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.post(
            f"/api/v1/move-note/{username}/{virtual_path}",
            data={"destination_folder": destination_folder},
        )

    if r.status_code != 200:
        return HTMLResponse("Move failed", status_code=500)

    return RedirectResponse(url=f"/notes/{destination_folder}", status_code=303)
