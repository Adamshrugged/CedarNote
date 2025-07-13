from fastapi import Request, APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx # type: ignore
import os
import traceback

router = APIRouter()
templates = Jinja2Templates(directory="templates")


from utilities.context_helpers import render_with_theme
from utilities.users import get_current_user
from utilities.api_client import call_internal_api


# -------------------- Delete folder --------------------
@router.post("/delete-folder")
async def delete_folder(request: Request, folder_path: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return HTMLResponse("Unauthorized", status_code=401)
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.delete(f"/api/v1/files/{user.email}/{folder_path}")
    return RedirectResponse(url="/notes", status_code=303)


# -------------------- Rename folder --------------------
@router.post("/rename-folder")
async def rename_folder_frontend(
    request: Request,
    current_path: str = Form(...),
    new_name: str = Form(...)
):
    user = get_current_user(request)
    if not user:
        return HTMLResponse("Unauthorized", status_code=401)

    # Debugging
    print(f"Received request to rename folder: {current_path} -> {new_name}")

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post(
            f"/api/v1/rename-folder/{user.email}",
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
async def delete_note_frontend(request: Request, virtual_path: str):
    user = get_current_user(request)
    if not user:
        return HTMLResponse("Unauthorized", status_code=401)

    try:
        await call_internal_api("DELETE", f"/api/v1/files/{user.email}/{virtual_path}")
    except Exception as e:
        return HTMLResponse(str(e), status_code=500)

    return RedirectResponse("/notes", status_code=303)


# -------------------- ROOT DIRECTORY: My Files --------------------
@router.get("/my-files", response_class=HTMLResponse)
async def list_notes(request: Request):

    user = get_current_user(request)
    if not user:
        return HTMLResponse("Unauthorized", status_code=401)

    # Call your own API
    try:
        entries = await call_internal_api("GET", f"/api/v1/files/{user.email}/")
    except Exception as e:
        return HTMLResponse(str(e), status_code=500)

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
        #"user": user,
        "notes": notes,
        "folders": folders
    })



# -------------------- BROWSING NOTES --------------------
@router.get("/notes/", response_class=HTMLResponse)
@router.get("/notes/{virtual_path:path}", response_class=HTMLResponse)
async def browse_notes(request: Request, virtual_path: str = ""):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)

    try:
        entries = await call_internal_api("GET", f"/api/v1/files/{user.email}/{virtual_path}")
    except Exception as e:
        traceback.print_exc()
        return HTMLResponse(f"Error loading notes: {str(e)}", status_code=500)

    # Case: it's a single note
    if isinstance(entries, dict) and entries.get("type") == "note":
        try:
            #folder_list = await call_internal_api("GET", f"/api/v1/folders/{username}")
            folder_list = await call_internal_api("GET", f"/api/v1/folders/{user.email}")
        except Exception:
            folder_list = []
        # Adding root
        folder_list.insert(0, "")

        metadata = entries.get("metadata", {})
        print( metadata.get("title") )
        display_title = metadata.get("title") or virtual_path.replace("_", " ")
        print( display_title )

        return render_with_theme(request, "view_note.html", {
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

    has_subfolders = any(e["type"] == "folder" for e in entries)

    # Build breadcrumbs
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
        "notes": notes,
        "folders": folders,
        "current_path": virtual_path,
        "breadcrumbs": breadcrumbs,
        "can_delete_folder": not has_subfolders
    })


