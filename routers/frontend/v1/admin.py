from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from sqlmodel import select, Session #type: ignore
from models.user import User
from models.db import engine, get_session #type: ignore
from pathlib import Path
from statistics import mean
import os


from utilities.context_helpers import render_with_theme
from utilities.users import get_current_user

from core.config import NOTES_DIR

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def calculate_stats(users):
    total_notes = 0
    stats = []

    for user in users:
        user_dir = Path(NOTES_DIR) / user.email
        note_count = 0

        if user_dir.exists():
            for root, dirs, files in os.walk(user_dir):
                note_count += sum(1 for f in files if f.endswith(".md"))

        total_notes += note_count
        stats.append({
            "email": user.email,
            "role": user.role,
            "note_count": note_count,
        })

    avg_notes = total_notes / len(users) if users else 0
    return {
        "user_count": len(users),
        "total_notes": total_notes,
        "avg_notes": round(avg_notes, 2),
        "user_stats": stats,
    }


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return HTMLResponse("Unauthorized", status_code=401)

    if getattr(user, "role", None) != "admin":
        return HTMLResponse("Forbidden", status_code=403)

    with Session(engine) as session:
        users = session.exec(select(User)).all()
        all_user_stats = calculate_stats(users)
        non_admin_users = [u for u in users if u.role != "admin"]
        non_admin_stats = calculate_stats(non_admin_users)

    return render_with_theme(request, "admin.html", {
        "user": user,
        "all_user_stats": all_user_stats,
        "non_admin_stats": non_admin_stats,
    })
