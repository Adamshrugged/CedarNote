from fastapi import Request, APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx # type: ignore
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")
from utilities.context_helpers import render_with_theme

@router.get("/new-folder", response_class=HTMLResponse)
async def new_folder_form(request: Request):
    username = "adam"  # Replace with session later

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.get(f"/api/v1/folders/{username}")
        folder_list = r.json() if r.status_code == 200 else []

    return render_with_theme(request, "new_folder.html", {
        "username": username,
        "username": username,
        "folders": folder_list
    })

@router.post("/create-folder")
async def create_folder_frontend(
    request: Request,
    folder_name: str = Form(...),
    parent_folder: str = Form(""),
):
    username = "adam"  # Replace with session later

    # Build full folder path
    folder_path = f"{parent_folder}/{folder_name}".strip("/") if parent_folder else folder_name

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post(
            f"/api/v1/folders/{username}",
            data={"folder_path": folder_path}  # ✅ what the API expects
        )

    if response.status_code != 200:
        return HTMLResponse("Error creating folder", status_code=500)

    return RedirectResponse("/notes", status_code=303)


