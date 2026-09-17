from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizhill_api.config import settings
from quizhill_api.db import get_db
from quizhill_api.models import User
from quizhill_api.schemas import AuthOut, GoogleAuthIn, UserOut
from quizhill_api.security import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, email=user.email, photo_url=user.photo_url)


def _verify_google_token(token: str) -> dict:
    audiences = settings.google_audiences
    if not audiences:
        raise HTTPException(status_code=503, detail="Brak GOOGLE_CLIENT_IDS — Google Auth nie jest skonfigurowane")
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    last_error: Exception | None = None
    for audience in audiences:
        try:
            return id_token.verify_oauth2_token(token, google_requests.Request(), audience)
        except Exception as exc:  # noqa: BLE001 — google-auth rzuca różne typy
            last_error = exc
    raise HTTPException(status_code=401, detail=f"Nie udało się zweryfikować tokenu Google: {last_error}")


@router.post("/google", response_model=AuthOut)
async def sign_in_with_google(payload: GoogleAuthIn, db: AsyncSession = Depends(get_db)) -> AuthOut:
    if settings.auth_dev_mode and payload.id_token.startswith("dev:"):
        info = {
            "sub": payload.id_token,
            "name": payload.name or "Dev User",
            "email": payload.email,
            "picture": payload.photo_url,
        }
    else:
        info = _verify_google_token(payload.id_token)

    google_sub = str(info.get("sub") or "")
    if not google_sub:
        raise HTTPException(status_code=401, detail="Token Google nie zawiera identyfikatora")

    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=str(uuid4()),
            google_sub=google_sub,
            name=str(info.get("name") or payload.name or "Gracz"),
            email=info.get("email") or payload.email,
            photo_url=info.get("picture") or payload.photo_url,
        )
        db.add(user)
    else:
        user.name = str(info.get("name") or user.name)
        user.email = info.get("email") or user.email
        user.photo_url = info.get("picture") or user.photo_url
    await db.commit()
    await db.refresh(user)
    return AuthOut(access_token=create_access_token(user.id), user=_user_out(user))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.post("/sign-out")
async def sign_out(user: User = Depends(get_current_user)) -> dict:
    return {"ok": True, "user_id": user.id}
