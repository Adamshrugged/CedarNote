from fastapi import Request, APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx # type: ignore
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")


from utilities.context_helpers import render_with_theme


# -------------------- Delete folder --------------------
@router.post("/delete-folder")
async def delete_folder(request: Request, folder_path: str = Form(...)):
    username = "adam"  # Replace with actual session logic
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.delete(f"/api/v1/files/{username}/{folder_path}")
    return RedirectResponse(url="/notes", status_code=303)


# -------------------- Rename folder --------------------
@router.post("/rename-folder")
async def rename_folder_frontend(
    request: Request,
    current_path: str = Form(...),
    new_name: str = Form(...)
):
    username = "adam"  # Replace with session or auth in the future

    # Debugging
    print(f"Received request to rename folder: {current_path} -> {new_name}")

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post(
            f"/api/v1/rename-folder/{username}",
            data={"current_path": current_path, "new_name": new_name}
        )

    if response.status_code != 200:
        print("Rename failed:", response.text)
        return RedirectResponse(f"/notes/{current_path}", status_code=303)

    # Build new path for redirect
    parent_path = os.path.dirname(current_path)
    new_virtual_path = f"{parent_path}/{new_name}".strip("/")
    return RedirectResponse(f"/notes/{new_virtual_path}", status_code=303)



# -------------------- Delete file --------------------
@router.post("/delete-note/{virtual_path:path}")
async def delete_note_frontend(virtual_path: str):
    username = "adam"  # Replace with session value later

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.delete(f"/api/v1/files/{username}/{virtual_path}")

    if response.status_code != 200:
        return HTMLResponse("Failed to delete note.", status_code=500)

    return RedirectResponse("/notes", status_code=303)


# -------------------- ROOT DIRECTORY: My Files --------------------
@router.get("/my-files", response_class=HTMLResponse)
async def list_notes(request: Request):
    username = "adam"
    #username = get_current_user(request)
    #if not username:
    #    return RedirectResponse("/register", status_code=302)

    # Call your own API
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.get(f"/api/v1/files/{username}/")
        if r.status_code != 200:
            return HTMLResponse("Error loading notes", status_code=500)
        entries = r.json()

    # Separate folders and notes for display
    folders = [
        {"name": e["name"], "path": f"/notes/{e['path']}"}
        for e in entries if e["type"] == "folder"
    ]

    notes = [
        {
            "name": e["name"],
            "path": f"/notes/{e['path']}",
            "metadata": e.get("metadata", {})
        }
        for e in entries if e["type"] == "note"
    ]

    return render_with_theme(request, "my_files.html", {
        "username": username,
        "notes": notes,
        "folders": folders
    })



# -------------------- BROWSING NOTES --------------------
@router.get("/notes/", response_class=HTMLResponse)
@router.get("/notes/{virtual_path:path}", response_class=HTMLResponse)
async def browse_notes(request: Request, virtual_path: str = ""):
    username = "adam"  # Replace with get_current_user(request) later

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.get(f"/api/v1/files/{username}/{virtual_path}")
        if r.status_code != 200:
            return HTMLResponse("Error loading", status_code=500)
        entries = r.json()

        # Case: it's a note
        if isinstance(entries, dict) and entries.get("type") == "note":
            r2 = await client.get(f"/api/v1/folders/{username}")
            folder_list = r2.json() if r2.status_code == 200 else []

            # Use metadata title if present
            metadata = entries.get("metadata", {})
            display_title = metadata.get("title") or virtual_path.replace("_", " ")


            return render_with_theme(request, "view_note.html", {
                "username": username,
                "note_content": entries["content"],
                "path": virtual_path,
                "folders": folder_list,
                "display_title": display_title
            })

    # Case: it's a folder (list of entries)
    folders = [
        {"name": e["name"], "path": f"/notes/{e['path']}"}
        for e in entries if e["type"] == "folder"
    ]

    notes = [
        {"name": e["name"], "path": f"/notes/{e['path']}"}
        for e in entries if e["type"] == "note"
    ]

    # Alert if it is a sub-folder
    has_subfolders = any(e["type"] == "folder" for e in entries)

    # Split virtual_path into parts for breadcrumbs
    breadcrumbs = []
    if virtual_path:
        parts = virtual_path.split("/")
        for i in range(len(parts)):
            crumb_path = "/".join(parts[:i+1])
            breadcrumbs.append({
                "name": parts[i],
                "path": f"/notes/{crumb_path}"
            })

    return render_with_theme(request, "my_files.html", {
        "username": username,
        "notes": notes,
        "folders": folders,
        "current_path": virtual_path,
        "breadcrumbs": breadcrumbs,
        "can_delete_folder": not has_subfolders
    })

