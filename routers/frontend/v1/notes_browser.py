from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import httpx # type: ignore

router = APIRouter()
templates = Jinja2Templates(directory="templates")
from utilities.context_helpers import render_with_theme
from utilities.users import get_current_user
from utilities.api_client import call_internal_api


# Create a new note - get to display the form and post to save the data
@router.get("/new-note", response_class=HTMLResponse)
async def new_note_form(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    
    today = datetime.today().strftime('%Y-%m-%d')

    try:
        folder_list = await call_internal_api("GET", f"/api/v1/folders/{user.email}")
    except Exception:
        folder_list = []

    return render_with_theme(request, "new_note.html", {
        "username": user.email,
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
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)

    # Sanitize title
    title = title.replace(" ", "_")

    # Virtual path is folder/title or just title
    virtual_path = f"{folder}/{title}" if folder else title

    try:
        await call_internal_api(
            "POST",
            f"/api/v1/create/{user.email}",
            data={"title": title, "folder": folder, "content": content}
        )
    except Exception:
        return RedirectResponse("/new-note", status_code=302)

    return RedirectResponse(f"/notes/{virtual_path}", status_code=303)


# Autosaving note
@router.post("/autosave-note/{virtual_path:path}")
async def autosave_note_frontend(request: Request, virtual_path: str):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.json()
    content = data.get("content", "")

    try:
        await call_internal_api(
            "POST",
            f"/api/v1/files/{user.email}/{virtual_path}",
            data={"content": content}
        )
        return JSONResponse({"status": "ok"})
    except Exception as e:
        print(f"Error saving {virtual_path}: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# Saving / updating a note
@router.post("/save-note/{virtual_path:path}")
async def save_note_frontend(request: Request, virtual_path: str, content: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)

    # Determine if this is a shared note and find the true owner
    original_owner = user.email
    resolved_path = virtual_path

    shared_info = await call_internal_api(
        "GET",
        f"/api/v1/share/resolve/{virtual_path}",
        headers={"x-user-email": user.email}
    )

    if shared_info.get("is_shared"):
        original_owner = shared_info["owner"]
        resolved_path = shared_info["path"]

    # Save the note to the true owner/path
    try:
        response = await call_internal_api(
            "POST",
            f"/api/v1/files/{original_owner}/{resolved_path}",
            data={"content": content}
        )
    except Exception:
        print(virtual_path)
        return RedirectResponse("/my-files", status_code=302)

    #return RedirectResponse(f"/notes/{virtual_path}", status_code=303)
    if shared_info.get("is_shared"):
        return RedirectResponse(f"/shared-note/{shared_info['owner']}/{shared_info['path']}", status_code=303)
    else:
        return RedirectResponse(f"/notes/{virtual_path}", status_code=303)




# Moving a note
@router.post("/move-note/{virtual_path:path}")
async def move_note_frontend(
    request: Request,
    virtual_path: str,
    destination_folder: str = Form("")
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)

    response = await call_internal_api(
        "POST",
        f"/api/v1/move-note/{user.email}/{virtual_path}",
        data={"destination_folder": destination_folder},
    )

    if "error" in response:
        return HTMLResponse(response["error"], status_code=500)


    return RedirectResponse(url=f"/notes/{destination_folder}", status_code=303)
