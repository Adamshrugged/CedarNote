from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from storage.filesystem import FileSystemStorage
import os

# Needed for sharing / friends
from sqlmodel import Session, select # type: ignore
from models.friend import FriendRequest
from models.shared import SharedNote
from models import db

from utilities.users import get_current_user
from utilities.api_client import verify_api_key

router = APIRouter()

def get_storage():
    return FileSystemStorage()


# Rename a folder
@router.post("/rename-folder/{user}")
def rename_folder(
    user: str,
    current_path: str = Form(...),
    new_name: str = Form(...),
    storage: FileSystemStorage = Depends(get_storage), 
    _: str = Depends(verify_api_key)
):
    print(f"Renaming folder: {current_path} -> {new_name}")

    success = storage.rename_folder(user=user, current_path=current_path, new_name=new_name)

    if not success:
        raise HTTPException(status_code=404, detail="Folder not found or rename failed")

    return {"status": "renamed", "old_path": current_path, "new_name": new_name}

# Create a new folder
@router.post("/folders/{user}")
def create_folder(
    user: str,
    folder_path: str = Form(...),
    storage: FileSystemStorage = Depends(get_storage), 
    _: str = Depends(verify_api_key)
):
    storage.create_folder(user=user, folder_path=folder_path)
    return {"status": "created", "path": folder_path}

# If the user doesn't have a folder, create it
@router.get("/files/{user}/")
def ensure_user_root_exists(user: str, storage: FileSystemStorage = Depends(get_storage), 
    _: str = Depends(verify_api_key)):
    """Ensure user's base folder exists (called after login)."""
    base_path = os.path.join(storage.root_dir, user)
    os.makedirs(base_path, exist_ok=True)
    
    # Optionally return list of entries (or just confirmation)
    return storage.list_folder(user, "")


# Get a list of folders for the user
@router.get("/folders/{user}")
async def get_all_folders(user: str, _: str = Depends(verify_api_key)):
    storage = get_storage()
    base_path = os.path.join(storage.root_dir, user)
    folder_list = []

    # Always include root
    #folder_list.append("")

    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            full = os.path.join(root, d)
            relative = os.path.relpath(full, base_path)
            folder_list.append(relative.replace("\\", "/"))  # normalize on Windows too

    print("Returning folders for user:", user)
    return folder_list


# Move a note
@router.post("/move-note/{user}/{virtual_path:path}")
def move_note(
    user: str,
    virtual_path: str,
    #destination_folder: str = Form(...),
    destination_folder: str = Form(""),
    storage: FileSystemStorage = Depends(get_storage), 
    _: str = Depends(verify_api_key)
):
    try:
        print(f"🔄 Attempting to move note for user: {user}")
        print(f"    Virtual path: {virtual_path}")
        print(f"    Destination:  {destination_folder}")
        storage.move_note(user=user, virtual_path=virtual_path, destination_folder=destination_folder)
        new_path = f"{destination_folder}/{os.path.basename(virtual_path)}"
        print(f"✅ Move complete: {new_path}")
        return {"status": "moved", "new_path": new_path}
    except Exception as e:
        print(f"❌ Move failed: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Router for getting shared notes
@router.get("/shared-note/{owner_email}/{note_path:path}")
async def read_shared_note(
    owner_email: str,
    note_path: str,
    request: Request,
    storage: FileSystemStorage = Depends(get_storage),
    _: str = Depends(verify_api_key)
):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check if shared with current user
    with Session(db.engine) as session:
        shared = session.exec(
            select(SharedNote).where(
                SharedNote.owner_email == owner_email,
                SharedNote.note_path == note_path,
                SharedNote.shared_with_email == current_user.email,
            )
        ).first()

        if not shared:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Serve the note content
    note = storage.get_note(owner_email, note_path)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


# Gets either the folder contents or the note if there's a match
@router.get("/files/{user}/{virtual_path:path}")
async def read_file_or_folder(user: str, virtual_path: str = "", storage: FileSystemStorage = Depends(get_storage), _: str = Depends(verify_api_key)):
    print(user)
    print(virtual_path)
    # Try to return file content first
    normalized_path = virtual_path if virtual_path.endswith(".md") else virtual_path + ".md"
    file_result = storage.get_note(user, normalized_path)
    if file_result:
        return file_result

    # If not a file, try to list folder
    folder_result = storage.list_folder(user, virtual_path)
    if folder_result is not None:
        return folder_result

    raise HTTPException(status_code=404, detail="Note or folder not found")

@router.post("/files/{user}/{virtual_path:path}")
def save_note(
    user: str,
    virtual_path: str,
    content: str = Form(...),
    storage: FileSystemStorage = Depends(get_storage), 
    _: str = Depends(verify_api_key)
):
    storage.save_note(user=user, virtual_path=virtual_path, content=content)
    return {"status": "saved", "path": virtual_path}


# Deletes a note or folder
@router.delete("/files/{user}/{virtual_path:path}")
def delete_note_or_folder(
    user: str,
    virtual_path: str,
    storage: FileSystemStorage = Depends(get_storage), 
    _: str = Depends(verify_api_key)
):
    # Try deleting a note first
    if storage.delete_note(user, virtual_path):
        return {"status": "deleted", "type": "note", "path": virtual_path}

    # Try deleting a folder
    if storage.delete_folder(user, virtual_path):
        return {"status": "deleted", "type": "folder", "path": virtual_path}

    raise HTTPException(status_code=404, detail="Note or folder not found")

# Create a new note
@router.post("/create/{user}")
def create_note(
    user: str,
    title: str = Form(...),
    folder: str = Form(""),
    content: str = Form(...),
    storage: FileSystemStorage = Depends(get_storage),
    _: str = Depends(verify_api_key)
):
    safe_title = title.strip().replace(" ", "_")
    virtual_path = f"{folder}/{safe_title}".strip("/") if folder else safe_title
    storage.save_note(user=user, virtual_path=virtual_path, content=content)
    return {"status": "created", "path": virtual_path}
