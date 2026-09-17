from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from quizhill_api.catalog import apply_quiz_filters, apply_quiz_sort, category_counts, load_quiz, play_out, quiz_out
from quizhill_api.db import get_db
from quizhill_api.models import Quiz
from quizhill_api.schemas import QuizOut, QuizPlayOut

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


@router.get("", response_model=list[QuizOut])
async def search_quizzes(
    name: str = "",
    category_id: str | None = None,
    kind: str | None = None,
    sort: str = "newest",
    ids: str | None = Query(default=None, description="Lista id oddzielona przecinkami"),
    db: AsyncSession = Depends(get_db),
) -> list[QuizOut]:
    counts = await category_counts(db)
    query = select(Quiz).options(selectinload(Quiz.category))
    if ids:
        wanted = [item.strip() for item in ids.split(",") if item.strip()]
        query = query.where(Quiz.id.in_(wanted))
    else:
        query = apply_quiz_filters(query, name=name, category_id=category_id, kind=kind)
        query = apply_quiz_sort(query, sort)
    result = await db.execute(query)
    return [quiz_out(quiz, counts) for quiz in result.scalars().all()]


@router.get("/{quiz_id}", response_model=QuizPlayOut)
async def get_quiz(quiz_id: str, db: AsyncSession = Depends(get_db)) -> QuizPlayOut:
    quiz = await load_quiz(db, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono quizu")
    counts = await category_counts(db)
    return play_out(quiz, counts)


home_router = APIRouter(prefix="/api/home", tags=["home"])


@home_router.get("/latest", response_model=list[QuizOut])
async def latest_quizzes(db: AsyncSession = Depends(get_db)) -> list[QuizOut]:
    counts = await category_counts(db)
    result = await db.execute(
        select(Quiz).options(selectinload(Quiz.category)).order_by(Quiz.created_at.desc()).limit(10)
    )
    return [quiz_out(quiz, counts) for quiz in result.scalars().all()]


@home_router.get("/popular", response_model=list[QuizOut])
async def popular_quizzes(db: AsyncSession = Depends(get_db)) -> list[QuizOut]:
    counts = await category_counts(db)
    result = await db.execute(
        select(Quiz).options(selectinload(Quiz.category)).order_by(Quiz.popularity.desc()).limit(10)
    )
    return [quiz_out(quiz, counts) for quiz in result.scalars().all()]


@home_router.get("/random", response_model=QuizOut)
async def random_quiz(
    exclude_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> QuizOut:
    counts = await category_counts(db)
    query = select(Quiz).options(selectinload(Quiz.category)).order_by(func.random())
    if exclude_id:
        query = query.where(Quiz.id != exclude_id)
    result = await db.execute(query.limit(1))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Brak quizów")
    return quiz_out(quiz, counts)
