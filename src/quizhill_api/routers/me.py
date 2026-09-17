from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from quizhill_api.db import get_db
from quizhill_api.models import Favorite, Play, PlayedQuiz, User
from quizhill_api.schemas import FavoriteOut, GameRecordIn, GameRecordOut, StatsIn, StatsOut
from quizhill_api.security import get_current_user

router = APIRouter(prefix="/api/me", tags=["me"])


async def _stats_for(db: AsyncSession, user: User) -> StatsOut:
    plays = await db.execute(select(Play).where(Play.user_id == user.id).order_by(Play.played_at.desc()))
    favorites = await db.execute(select(Favorite).where(Favorite.user_id == user.id))
    played = await db.execute(select(PlayedQuiz).where(PlayedQuiz.user_id == user.id))
    return StatsOut(
        history=[
            GameRecordOut(quiz_id=item.quiz_id, score=item.score, total=item.total, played_at=item.played_at)
            for item in plays.scalars().all()
        ],
        favorite_ids=[item.quiz_id for item in favorites.scalars().all()],
        played_ids=[item.quiz_id for item in played.scalars().all()],
    )


@router.get("/stats")
async def get_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    stats = await _stats_for(db, user)
    return {"is_first_login": not user.stats_initialized, **stats.model_dump(mode="json")}


async def _replace_stats(db: AsyncSession, user: User, payload: StatsIn) -> None:
    await db.execute(delete(Play).where(Play.user_id == user.id))
    await db.execute(delete(Favorite).where(Favorite.user_id == user.id))
    await db.execute(delete(PlayedQuiz).where(PlayedQuiz.user_id == user.id))
    await db.flush()
    for record in payload.history[:50]:
        db.add(
            Play(
                user_id=user.id,
                quiz_id=record.quiz_id,
                score=record.score,
                total=record.total,
                played_at=record.played_at or datetime.now(UTC),
            )
        )
    for quiz_id in dict.fromkeys(payload.favorite_ids):
        db.add(Favorite(user_id=user.id, quiz_id=quiz_id))
    played_ids = set(payload.played_ids) | {item.quiz_id for item in payload.history}
    for quiz_id in played_ids:
        db.add(PlayedQuiz(user_id=user.id, quiz_id=quiz_id))
    user.stats_initialized = True


@router.put("/stats", response_model=StatsOut)
async def save_stats(
    payload: StatsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatsOut:
    await _replace_stats(db, user, payload)
    await db.commit()
    return await _stats_for(db, user)


@router.delete("/stats", response_model=StatsOut)
async def clear_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> StatsOut:
    await _replace_stats(db, user, StatsIn())
    await db.commit()
    return await _stats_for(db, user)


@router.post("/plays", response_model=StatsOut)
async def record_play(
    payload: GameRecordIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatsOut:
    db.add(
        Play(
            user_id=user.id,
            quiz_id=payload.quiz_id,
            score=payload.score,
            total=payload.total,
            played_at=payload.played_at or datetime.now(UTC),
        )
    )
    existing = await db.execute(
        select(PlayedQuiz).where(PlayedQuiz.user_id == user.id, PlayedQuiz.quiz_id == payload.quiz_id)
    )
    if existing.scalar_one_or_none() is None:
        db.add(PlayedQuiz(user_id=user.id, quiz_id=payload.quiz_id))
    user.stats_initialized = True
    await db.commit()
    return await _stats_for(db, user)


@router.put("/favorites/{quiz_id}", response_model=FavoriteOut)
async def toggle_favorite(
    quiz_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FavoriteOut:
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.quiz_id == quiz_id))
    current = result.scalar_one_or_none()
    if current is None:
        db.add(Favorite(user_id=user.id, quiz_id=quiz_id))
        favorite = True
    else:
        await db.delete(current)
        favorite = False
    user.stats_initialized = True
    await db.commit()
    return FavoriteOut(quiz_id=quiz_id, favorite=favorite)
