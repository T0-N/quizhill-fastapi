from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizhill_api.catalog import category_counts, category_out
from quizhill_api.db import get_db
from quizhill_api.models import Category
from quizhill_api.schemas import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    counts = await category_counts(db)
    result = await db.execute(select(Category).order_by(Category.title))
    return [category_out(category, counts) for category in result.scalars().all()]
