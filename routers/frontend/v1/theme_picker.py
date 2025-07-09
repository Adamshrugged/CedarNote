from starlette.status import HTTP_303_SEE_OTHER
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.post("/set-theme")
async def set_theme(request: Request, theme: str = Form(...)):
    response = RedirectResponse(request.headers.get("referer", "/"), status_code=303)
    response.set_cookie(key="theme", value=theme, max_age=60 * 60 * 24 * 30)  # 30 days
    return response
