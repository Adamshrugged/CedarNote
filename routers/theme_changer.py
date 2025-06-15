from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.post("/set-theme")
async def set_theme(request: Request, theme: str = Form(...)):
    referrer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referrer, status_code=303)
    response.set_cookie("theme", theme)
    return response
