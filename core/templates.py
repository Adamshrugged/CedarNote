# core/templates.py
from fastapi import Request
from fastapi.templating import Jinja2Templates
from core.config import ACTIVE_THEME
import os

#templates = Jinja2Templates(directory=f"templates/themes/{ACTIVE_THEME}")

THEME_DIR = "templates/themes"
AVAILABLE_THEMES = [
    name for name in os.listdir(THEME_DIR)
    if os.path.isdir(os.path.join(THEME_DIR, name))
]

def sanitize_theme(raw_theme: str) -> str:
    if raw_theme in AVAILABLE_THEMES:
        return raw_theme
    return "default"

# Helper function to change the themes
def get_theme(request: Request) -> str:
    raw = request.cookies.get("theme", "default")
    return sanitize_theme(raw)

def get_templates(theme: str) -> Jinja2Templates:
    return Jinja2Templates(directory=f"templates/themes/{theme}")

templates = get_templates(ACTIVE_THEME)