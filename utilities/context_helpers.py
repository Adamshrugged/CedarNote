from fastapi import Request

# --------------------- Helper Functions ---------------------
from utilities.file_ops import get_notes_shared_with
from utilities.formatting import parse_frontmatter
from utilities.build_folder_tree import build_folder_tree
from utilities.users import get_current_user, is_superuser
from core.config import NOTES_DIR, AUTH_REQUIRED
from core.templates import templates, get_theme, AVAILABLE_THEMES


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
