# core/templates.py
from fastapi.templating import Jinja2Templates
from core.config import ACTIVE_THEME

templates = Jinja2Templates(directory=f"templates/themes/{ACTIVE_THEME}")
