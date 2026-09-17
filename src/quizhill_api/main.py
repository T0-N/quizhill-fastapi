from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quizhill_api.config import settings
from quizhill_api.db import Base, SessionLocal, engine
from quizhill_api import models as _models  # noqa: F401
from quizhill_api.routers.admin import router as admin_router
from quizhill_api.routers.auth import router as auth_router
from quizhill_api.routers.categories import router as categories_router
from quizhill_api.routers.me import router as me_router
from quizhill_api.routers.quizzes import home_router, router as quizzes_router
from quizhill_api.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.seed_on_empty:
        async with SessionLocal() as session:
            await seed_if_empty(session)
    yield
    await engine.dispose()


app = FastAPI(title="Quizhill API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(categories_router)
app.include_router(quizzes_router)
app.include_router(home_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(admin_router)


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True}


def run() -> None:
    import uvicorn

    uvicorn.run("quizhill_api.main:app", host="0.0.0.0", port=8000, reload=True)


def main() -> None:
    run()
