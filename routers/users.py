from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.hash import bcrypt
import os, json

router = APIRouter()
from core.config import NOTES_DIR, USERS_FILE, AUTH_REQUIRED
from core.templates import templates, get_theme, AVAILABLE_THEMES

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    theme = get_theme(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        })

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = load_users()
    if username not in users or not bcrypt.verify(password, users[username]["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["username"] = username
    return RedirectResponse("/", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")





@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    # If authentication setup, go to auth/login
    if not AUTH_REQUIRED:
        return RedirectResponse("/auth/login")
    
    # Otherwise proceed as normal
    theme = get_theme(request)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "theme": theme,
        "available_themes": AVAILABLE_THEMES,
        })

@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists")

    # First user becomes superuser
    is_superuser = len(users) == 0

    users[username] = {
        "password": bcrypt.hash(password),
        "is_superuser": is_superuser
    }
    save_users(users)

    os.makedirs(os.path.join(NOTES_DIR, username), exist_ok=True)

    return RedirectResponse("/login", status_code=303)
