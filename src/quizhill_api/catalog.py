from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from quizhill_api.models import Category, Quiz
from quizhill_api.schemas import (
    CategoryOut,
    ChoiceQuestionOut,
    ListContentOut,
    QuizOut,
    QuizPlayOut,
)


async def category_counts(db: AsyncSession) -> dict[str, int]:
    rows = await db.execute(select(Quiz.category_id, func.count(Quiz.id)).group_by(Quiz.category_id))
    return {category_id: count for category_id, count in rows.all()}


def category_out(category: Category, counts: dict[str, int]) -> CategoryOut:
    return CategoryOut(
        id=category.id,
        title=category.title,
        description=category.description,
        image_url=category.image_url,
        icon=category.icon,
        quiz_count=counts.get(category.id, 0),
    )


def quiz_out(quiz: Quiz, counts: dict[str, int] | None = None) -> QuizOut:
    counts = counts or {}
    return QuizOut(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        details=quiz.details,
        image_url=quiz.image_url,
        category=category_out(quiz.category, counts),
        kind=quiz.kind,
        created_at=quiz.created_at,
        popularity=quiz.popularity,
        time_seconds=quiz.time_seconds,
        audio_url=quiz.audio_url,
    )


def play_out(quiz: Quiz, counts: dict[str, int] | None = None) -> QuizPlayOut:
    list_content = None
    if quiz.kind in {"list", "listMusical"}:
        list_content = ListContentOut(
            prompt=quiz.list_prompt or quiz.title,
            image_url=quiz.list_image_url or quiz.image_url,
            answers=list(quiz.list_answers or []),
        )
    questions = [
        ChoiceQuestionOut(
            prompt=question.prompt,
            image_url=question.image_url,
            options=list(question.options),
            correct_index=question.correct_index,
        )
        for question in quiz.choice_questions
    ]
    return QuizPlayOut(
        quiz=quiz_out(quiz, counts),
        audio_url=quiz.audio_url,
        choice_questions=questions,
        list_content=list_content,
    )


def apply_quiz_filters(query, *, name: str = "", category_id: str | None = None, kind: str | None = None):
    needle = name.strip().lower()
    if needle:
        like = f"%{needle}%"
        query = query.where(func.lower(Quiz.title).like(like) | func.lower(Quiz.description).like(like))
    if category_id:
        query = query.where(Quiz.category_id == category_id)
    if kind:
        query = query.where(Quiz.kind == kind)
    return query


def apply_quiz_sort(query, sort: str):
    mapping = {
        "newest": Quiz.created_at.desc(),
        "oldest": Quiz.created_at.asc(),
        "nameAsc": Quiz.title.asc(),
        "nameDesc": Quiz.title.desc(),
        "popularityDesc": Quiz.popularity.desc(),
        "popularityAsc": Quiz.popularity.asc(),
    }
    return query.order_by(mapping.get(sort, Quiz.created_at.desc()))


async def load_quizzes(db: AsyncSession) -> list[Quiz]:
    result = await db.execute(select(Quiz).options(selectinload(Quiz.category)))
    return list(result.scalars().all())


async def load_quiz(db: AsyncSession, quiz_id: str) -> Quiz | None:
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.category), selectinload(Quiz.choice_questions))
        .where(Quiz.id == quiz_id)
    )
    return result.scalar_one_or_none()
