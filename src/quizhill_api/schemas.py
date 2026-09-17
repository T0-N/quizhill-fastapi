from datetime import datetime

from pydantic import BaseModel, Field


QUIZ_KINDS = ("choice", "choiceMusical", "list", "listMusical")
QUIZ_SORTS = (
    "newest",
    "oldest",
    "nameAsc",
    "nameDesc",
    "popularityDesc",
    "popularityAsc",
)


class CategoryOut(BaseModel):
    id: str
    title: str
    description: str
    image_url: str
    icon: str
    quiz_count: int = 0


class QuizOut(BaseModel):
    id: str
    title: str
    description: str
    details: str | None = None
    image_url: str | None = None
    category: CategoryOut
    kind: str
    played: bool = False
    created_at: datetime
    popularity: int
    time_seconds: int
    audio_url: str | None = None


class ChoiceQuestionOut(BaseModel):
    prompt: str
    image_url: str | None = None
    options: list[str]
    correct_index: int


class ListContentOut(BaseModel):
    prompt: str
    image_url: str | None = None
    answers: list[str]


class QuizPlayOut(BaseModel):
    quiz: QuizOut
    audio_url: str | None = None
    choice_questions: list[ChoiceQuestionOut] = Field(default_factory=list)
    list_content: ListContentOut | None = None


class GoogleAuthIn(BaseModel):
    id_token: str
    name: str | None = None
    email: str | None = None
    photo_url: str | None = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str | None = None
    photo_url: str | None = None


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class GameRecordIn(BaseModel):
    quiz_id: str
    score: int
    total: int
    played_at: datetime | None = None


class GameRecordOut(BaseModel):
    quiz_id: str
    score: int
    total: int
    played_at: datetime


class StatsOut(BaseModel):
    history: list[GameRecordOut] = Field(default_factory=list)
    favorite_ids: list[str] = Field(default_factory=list)
    played_ids: list[str] = Field(default_factory=list)


class StatsIn(BaseModel):
    history: list[GameRecordIn] = Field(default_factory=list)
    favorite_ids: list[str] = Field(default_factory=list)
    played_ids: list[str] = Field(default_factory=list)


class FavoriteOut(BaseModel):
    quiz_id: str
    favorite: bool
