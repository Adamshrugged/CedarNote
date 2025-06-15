import os
import pathlib
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from utilities.users import require_login
from utilities.file_ops import resolve_safe_path

NOTES_DIR = "notes"
router = APIRouter()

@router.post("/autosave-note/{path:path}")
async def autosave_note(request: Request, path: str):
    username = require_login(request)
    if isinstance(username, JSONResponse):  # fallback if you want to redirect
        raise HTTPException(status_code=401, detail="Not authenticated")

    decoded_path = unquote(path)
    user_notes_dir = os.path.join(NOTES_DIR, username)

    try:
        safe_path = resolve_safe_path(user_notes_dir, decoded_path)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        data = await request.json()
        content = data.get("content", "")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    safe_path.write_text(content, encoding="utf-8")

    return JSONResponse(content={"status": "saved"})
