
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from urllib.parse import unquote
import pathlib


NOTES_DIR = "notes"
os.makedirs(NOTES_DIR, exist_ok=True)

router = APIRouter()

# Auto save edits
@router.post("/autosave-note/{path:path}")
async def autosave_note(path: str, request: Request):
    decoded_path = unquote(path)
    safe_path = pathlib.Path(NOTES_DIR) / decoded_path

    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        data = await request.json()
        content = data.get("content", "")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    safe_path.write_text(content, encoding="utf-8")

    return JSONResponse(content={"status": "saved"})