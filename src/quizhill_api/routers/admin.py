from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.status import HTTP_303_SEE_OTHER

from quizhill_api.config import settings
from quizhill_api.db import get_db
from quizhill_api.models import Category, ChoiceQuestion, Quiz
from quizhill_api.schemas import QUIZ_KINDS

router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

ADMIN_COOKIE = "quizhill_admin"


def _authed(request: Request) -> bool:
    return request.cookies.get(ADMIN_COOKIE) == settings.admin_password


def _require_admin(request: Request) -> None:
    if not _authed(request):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin_login.html",
        {"error": None},
    )


@router.post("/admin/login")
async def admin_login(password: str = Form(...)) -> RedirectResponse:
    if password != settings.admin_password:
        response = RedirectResponse("/admin/login?bad=1", status_code=HTTP_303_SEE_OTHER)
        return response
    response = RedirectResponse("/admin", status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(ADMIN_COOKIE, password, httponly=True, samesite="lax")
    return response


@router.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    if not _authed(request):
        return RedirectResponse("/admin/login", status_code=HTTP_303_SEE_OTHER)
    categories = (await db.execute(select(Category).order_by(Category.title))).scalars().all()
    quizzes = (
        await db.execute(select(Quiz).options(selectinload(Quiz.category)).order_by(Quiz.created_at.desc()))
    ).scalars().all()
    return templates.TemplateResponse(
        request,
        "admin_home.html",
        {"categories": categories, "quizzes": quizzes, "kinds": QUIZ_KINDS, "saved": request.query_params.get("saved")},
    )


@router.post("/admin/categories")
async def admin_add_category(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    icon: str = Form("quiz_outlined"),
    category_id: str = Form(""),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if not _authed(request):
        return RedirectResponse("/admin/login", status_code=HTTP_303_SEE_OTHER)
    slug = (category_id or title).strip().lower().replace(" ", "-")
    existing = await db.get(Category, slug)
    if existing is None:
        db.add(
            Category(
                id=slug,
                title=title.strip(),
                description=description.strip() or title.strip(),
                image_url=image_url.strip() or f"https://picsum.photos/seed/quizhill-{slug}/400/280",
                icon=icon.strip() or "quiz_outlined",
            )
        )
        await db.commit()
    return RedirectResponse("/admin?saved=kategoria", status_code=HTTP_303_SEE_OTHER)


@router.post("/admin/quizzes")
async def admin_add_quiz(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    category_id: str = Form(...),
    kind: str = Form("choice"),
    time_seconds: int = Form(6),
    image_url: str = Form(""),
    audio_url: str = Form(""),
    details: str = Form(""),
    list_prompt: str = Form(""),
    list_answers: str = Form(""),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if not _authed(request):
        return RedirectResponse("/admin/login", status_code=HTTP_303_SEE_OTHER)
    if kind not in QUIZ_KINDS:
        kind = "choice"
    quiz_id = str(uuid4())[:8]
    is_list = kind.startswith("list")
    answers = [line.strip() for line in list_answers.splitlines() if line.strip()]
    quiz = Quiz(
        id=quiz_id,
        title=title.strip(),
        description=description.strip() or title.strip(),
        details=details.strip() or None,
        image_url=image_url.strip() or None,
        category_id=category_id,
        kind=kind,
        popularity=0,
        time_seconds=time_seconds or (90 if is_list else 6),
        audio_url=audio_url.strip() or None,
        list_prompt=list_prompt.strip() or None,
        list_image_url=image_url.strip() or None,
        list_answers=answers if is_list else None,
    )
    db.add(quiz)
    await db.flush()

    if not is_list:
        form = await request.form()
        for index in range(12):
            prompt = str(form.get(f"q{index}_prompt") or "").strip()
            if not prompt:
                continue
            options = [
                str(form.get(f"q{index}_a") or "").strip(),
                str(form.get(f"q{index}_b") or "").strip(),
                str(form.get(f"q{index}_c") or "").strip(),
                str(form.get(f"q{index}_d") or "").strip(),
            ]
            if any(not option for option in options):
                continue
            try:
                correct = int(str(form.get(f"q{index}_correct") or "0"))
            except ValueError:
                correct = 0
            db.add(
                ChoiceQuestion(
                    quiz_id=quiz.id,
                    prompt=prompt,
                    image_url=image_url.strip() or None,
                    options=options,
                    correct_index=max(0, min(correct, 3)),
                    sort_order=index,
                )
            )
    await db.commit()
    return RedirectResponse("/admin?saved=quiz", status_code=HTTP_303_SEE_OTHER)
