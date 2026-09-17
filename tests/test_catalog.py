import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.asyncio
async def test_categories_include_counts(client):
    response = await client.get("/api/categories")
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 7
    przyroda = next(item for item in categories if item["id"] == "przyroda")
    assert przyroda["quiz_count"] == 3
    assert przyroda["title"] == "Przyroda"


@pytest.mark.asyncio
async def test_home_latest_and_popular(client):
    latest = (await client.get("/api/home/latest")).json()
    popular = (await client.get("/api/home/popular")).json()
    assert latest[0]["id"] == "1"
    assert popular[0]["id"] == "7"
    assert len(latest) == 10
    assert len(popular) == 10


@pytest.mark.asyncio
async def test_random_can_exclude(client):
    seen = set()
    for _ in range(8):
        quiz = (await client.get("/api/home/random", params={"exclude_id": "1"})).json()
        seen.add(quiz["id"])
        assert quiz["id"] != "1"
    assert seen


@pytest.mark.asyncio
async def test_search_filters_and_sort(client):
    rivers = (await client.get("/api/quizzes", params={"name": "rzeki"})).json()
    assert [item["id"] for item in rivers] == ["4"]

    slask = (await client.get("/api/quizzes", params={"category_id": "slask"})).json()
    assert {item["id"] for item in slask} == {"3", "10"}

    lists = (await client.get("/api/quizzes", params={"kind": "list", "sort": "nameAsc"})).json()
    titles = [item["title"] for item in lists]
    assert titles == sorted(titles)

    by_ids = (await client.get("/api/quizzes", params={"ids": "5,7"})).json()
    assert {item["id"] for item in by_ids} == {"5", "7"}


@pytest.mark.asyncio
async def test_play_content_choice_and_list(client):
    choice = (await client.get("/api/quizzes/1")).json()
    assert choice["quiz"]["kind"] == "choice"
    assert len(choice["choice_questions"]) == 6
    assert choice["choice_questions"][0]["correct_index"] == 0

    listed = (await client.get("/api/quizzes/2")).json()
    assert listed["list_content"]["answers"][0] == "Paryż"
    assert listed["quiz"]["time_seconds"] == 120

    missing = await client.get("/api/quizzes/missing")
    assert missing.status_code == 404
