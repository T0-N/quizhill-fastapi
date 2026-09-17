import pytest


async def _login(client, suffix="1"):
    response = await client.post(
        "/api/auth/google",
        json={
            "id_token": f"dev:user-{suffix}",
            "name": "Anna Test",
            "email": f"anna{suffix}@example.com",
        },
    )
    assert response.status_code == 200
    body = response.json()
    return body["access_token"], body["user"]


@pytest.mark.asyncio
async def test_google_dev_login_and_me(client):
    token, user = await _login(client)
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["name"] == "Anna Test"
    assert user["email"] == "anna1@example.com"


@pytest.mark.asyncio
async def test_stats_first_login_then_sync(client):
    token, _ = await _login(client, "stats")
    headers = {"Authorization": f"Bearer {token}"}
    first = (await client.get("/api/me/stats", headers=headers)).json()
    assert first["is_first_login"] is True
    saved = await client.put(
        "/api/me/stats",
        headers=headers,
        json={
            "history": [
                {
                    "quiz_id": "1",
                    "score": 5,
                    "total": 6,
                    "played_at": "2026-09-17T10:00:00+00:00",
                }
            ],
            "favorite_ids": ["2"],
            "played_ids": ["1"],
        },
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["favorite_ids"] == ["2"]
    assert body["played_ids"] == ["1"]
    assert body["history"][0]["score"] == 5

    second = (await client.get("/api/me/stats", headers=headers)).json()
    assert second["is_first_login"] is False


@pytest.mark.asyncio
async def test_play_favorite_and_clear(client):
    token, _ = await _login(client, "play")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/me/plays",
        headers=headers,
        json={"quiz_id": "3", "score": 4, "total": 6},
    )
    fav = (await client.put("/api/me/favorites/3", headers=headers)).json()
    assert fav["favorite"] is True
    unfav = (await client.put("/api/me/favorites/3", headers=headers)).json()
    assert unfav["favorite"] is False
    cleared = (await client.delete("/api/me/stats", headers=headers)).json()
    assert cleared["history"] == []
    assert cleared["favorite_ids"] == []
    assert cleared["played_ids"] == []
