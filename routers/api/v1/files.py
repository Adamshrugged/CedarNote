from fastapi import APIRouter, Depends, HTTPException, Form
from storage.filesystem import FileSystemStorage
import os

router = APIRouter()

def get_storage():
    return FileSystemStorage()


# Rename a folder
@router.post("/rename-folder/{user}")
def rename_folder(
    user: str,
    current_path: str = Form(...),
    new_name: str = Form(...),
    storage: FileSystemStorage = Depends(get_storage)
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
    storage: FileSystemStorage = Depends(get_storage)
):
    storage.create_folder(user=user, folder_path=folder_path)
    return {"status": "created", "path": folder_path}


# Get a list of folders for the user
@router.get("/folders/{user}")
def get_all_folders(user: str):
    storage = get_storage()
    base_path = os.path.join(storage.root_dir, user)
    folder_list = []

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
    destination_folder: str = Form(...),
    storage: FileSystemStorage = Depends(get_storage)
):
    storage.move_note(user=user, virtual_path=virtual_path, destination_folder=destination_folder)
    return {"status": "moved", "new_path": f"{destination_folder}/{os.path.basename(virtual_path)}"}



# Gets either the folder contents or the note if there's a match
@router.get("/files/{user}/{virtual_path:path}")
def read_file_or_folder(user: str, virtual_path: str = "", storage: FileSystemStorage = Depends(get_storage)):
    # Try to return file content first
    file_result = storage.get_note(user, virtual_path)
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
    storage: FileSystemStorage = Depends(get_storage)
):
    storage.save_note(user=user, virtual_path=virtual_path, content=content)
    return {"status": "saved", "path": virtual_path}


# Deletes a note or folder
@router.delete("/files/{user}/{virtual_path:path}")
def delete_note_or_folder(
    user: str,
    virtual_path: str,
    storage: FileSystemStorage = Depends(get_storage)
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
):
    safe_title = title.strip().replace(" ", "_")
    virtual_path = f"{folder}/{safe_title}".strip("/") if folder else safe_title
    storage.save_note(user=user, virtual_path=virtual_path, content=content)
    return {"status": "created", "path": virtual_path}
