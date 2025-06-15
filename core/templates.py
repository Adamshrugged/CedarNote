# core/templates.py
from fastapi import Request
from fastapi.templating import Jinja2Templates
import os

TEMPLATE_DIR = "templates"  # All HTML templates go here
THEME_DIR = os.path.join(TEMPLATE_DIR, "themes")

AVAILABLE_THEMES = [
    name for name in os.listdir(THEME_DIR)
    if os.path.isdir(os.path.join(THEME_DIR, name))
]

def sanitize_theme(raw_theme: str) -> str:
    return raw_theme if raw_theme in AVAILABLE_THEMES else "default"

def get_theme(request: Request) -> str:
    raw = request.cookies.get("theme", "default")
    return sanitize_theme(raw)

templates = Jinja2Templates(directory=TEMPLATE_DIR)
