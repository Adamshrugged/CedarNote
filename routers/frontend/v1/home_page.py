from pathlib import Path
from fastapi import Request, APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension


router = APIRouter()
templates = Jinja2Templates(directory="templates")

from utilities.context_helpers import render_with_theme


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    md_path = Path("page_md/home_page.md")
    if md_path.exists():
        raw_md = md_path.read_text(encoding="utf-8")
        html_content = markdown.markdown(raw_md, extensions=["fenced_code", "codehilite", "extra"])

    else:
        html_content = "<h1>Welcome</h1><p>Home page not found.</p>"

    return render_with_theme(request, "home_page.html", {
        "content": html_content
    })
