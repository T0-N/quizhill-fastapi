import pytest


@pytest.mark.asyncio
async def test_admin_adds_category_and_list_quiz(client):
    login = await client.post("/admin/login", data={"password": "quizhill"}, follow_redirects=False)
    assert login.status_code == 303

    added = await client.post(
        "/admin/categories",
        data={
            "title": "Testowa",
            "description": "Kategoria z panelu",
            "image_url": "",
            "icon": "quiz_outlined",
        },
        follow_redirects=False,
    )
    assert added.status_code == 303

    quiz = await client.post(
        "/admin/quizzes",
        data={
            "title": "Hasła testowe",
            "description": "Lista z panelu",
            "category_id": "testowa",
            "kind": "list",
            "time_seconds": "90",
            "image_url": "",
            "audio_url": "",
            "details": "",
            "list_prompt": "Wpisz owoce",
            "list_answers": "Jabłko\nGruszka\nŚliwka",
        },
        follow_redirects=False,
    )
    assert quiz.status_code == 303

    categories = (await client.get("/api/categories")).json()
    assert any(item["title"] == "Testowa" for item in categories)
    found = (await client.get("/api/quizzes", params={"name": "Hasła testowe"})).json()
    assert len(found) == 1
    play = (await client.get(f"/api/quizzes/{found[0]['id']}")).json()
    assert play["list_content"]["answers"] == ["Jabłko", "Gruszka", "Śliwka"]
