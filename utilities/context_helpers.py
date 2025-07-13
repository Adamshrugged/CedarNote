from fastapi import Request
from fastapi.templating import Jinja2Templates
import os

# Database information
from sqlmodel import Session, select # type: ignore
from models.db import engine
from models.user import User


# --------------------- Helper Functions ---------------------
from utilities.file_ops import get_notes_shared_with
from utilities.formatting import parse_frontmatter
from utilities.build_folder_tree import build_folder_tree
from utilities.users import get_current_user, is_superuser
from utilities.theme import get_template_context
from core.config import NOTES_DIR, AUTH_REQUIRED
from core.templates import templates, get_theme, AVAILABLE_THEMES

templates = Jinja2Templates(directory="templates")

def get_template_context(request: Request) -> dict:
    theme = request.cookies.get("theme", "default")

    themes_dir = os.path.join("templates", "themes")
    try:
        available_themes = [
            name for name in os.listdir(themes_dir)
            if os.path.isdir(os.path.join(themes_dir, name)) and
               os.path.isfile(os.path.join(themes_dir, name, "style.css"))
        ]
    except FileNotFoundError:
        available_themes = ["default"]

    session_user = request.session.get("user")
    db_user = None
    if session_user and session_user.get("email"):
        with Session(engine) as session:
            result = session.exec(select(User).where(User.email == session_user["email"]))
            db_user = result.first()

    return {
        "request": request,
        "theme": theme,
        "available_themes": available_themes,
        "user": db_user
    }

def render_with_theme(request: Request, template_name: str, context: dict):
    context.update(get_template_context(request))
    return templates.TemplateResponse(template_name, context)

"""
def base_context(request: Request, extra: dict = None) -> dict:
    username = get_current_user(request)
    theme = get_theme(request)
    context = {
        "request": request,
        "username": username,
        "is_superuser": is_superuser(username),
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        "AUTH_REQUIRED": AUTH_REQUIRED
    }
    if extra:
        context.update(extra)
    return context
    """
