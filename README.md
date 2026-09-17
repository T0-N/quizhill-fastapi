# Quizhill API

Backend aplikacji Android Quizhill: **Python 3.14**, **FastAPI**, **SQLAlchemy 2 (async)**, **PostgreSQL 16**, **uv**.

Aplikacja Flutter jest źródłem funkcji. API obsługuje:

- kategorie i wyszukiwanie quizów
- ekran Dom (najnowsze, popularne, losowy)
- treść rozgrywki ABCD / lista / warianty dźwiękowe
- konto Google (JWT) oraz historię, ulubione i rozegrane quizy
- prosty panel HTML do dodawania kategorii i quizów (`/admin`)

## Uruchomienie lokalne

Wymagane: Docker Desktop, Python 3.12+ (tu 3.14), [uv](https://docs.astral.sh/uv/).

```bash
cd quizhill-fastapi
copy .env.example .env
docker compose up -d
uv sync
uv run quizhill-api
```

API: http://127.0.0.1:8000  
Dokumentacja: http://127.0.0.1:8000/docs  
Panel dla osoby nietechnicznej: http://127.0.0.1:8000/admin  
Hasło panelu z `.env`: `ADMIN_PASSWORD` (domyślnie `quizhill`).

Emulator Androida łączy się z hostem przez `http://10.0.2.2:8000`.

## Testy

```bash
uv run pytest
```

Testy używają SQLite w pamięci i nie potrzebują Dockera.

## Neon (produkcja)

Ustaw `DATABASE_URL` na connection string Neon, z driverem async:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/DB?ssl=require
```

Lokalny Docker stawia PostgreSQL **16**, czyli tę samą major wersję, której używa Neon. Schemat tworzy się automatycznie przy starcie (`create_all` + seed, gdy baza jest pusta).

## Logowanie Google

Flutter wysyła `id_token` na `POST /api/auth/google`. Żeby weryfikacja działała, w `.env` ustaw `GOOGLE_CLIENT_IDS` (Web client ID oraz Android client ID, po przecinku) i `AUTH_DEV_MODE=false`.

Lokalnie `AUTH_DEV_MODE=true` pozwala testować endpoint tokenem `dev:...` bez Google.
