def create_story(client):
    response = client.post("/api/v1/stories", json={"title": "记忆拍卖场", "idea": "失忆鉴定师发现过去被拍卖。"})
    assert response.status_code == 201
    return response.json()


def test_author_can_create_and_retrieve_an_idea_without_generation_overwriting_it(client):
    story = create_story(client)

    generated = client.post(
        f"/api/v1/stories/{story['id']}/generations",
        json={"action": "generate_concept"},
    )
    retrieved = client.get(f"/api/v1/stories/{story['id']}")

    assert generated.status_code == 200
    assert generated.json()["status"] == "succeeded"
    assert retrieved.json()["idea"] == "失忆鉴定师发现过去被拍卖。"
    assert retrieved.json()["status"] == "idea_draft"


def test_author_can_confirm_a_locked_concept_and_locked_field_cannot_be_changed(client):
    story = create_story(client)
    concept = {"genre": "科幻悬疑", "synopsis": "鉴定师追查被拍卖的记忆。"}
    confirmed = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": concept, "locked_paths": ["genre"], "expected_version": 1, "status": "confirmed"},
    )
    changed = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": {**concept, "genre": "奇幻"}, "expected_version": 2, "status": "confirmed"},
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["locked_paths"] == ["genre"]
    assert changed.status_code == 409
    assert client.get(f"/api/v1/stories/{story['id']}").json()["status"] == "concept_confirmed"


def test_stale_concept_version_is_rejected_without_overwriting_history(client):
    story = create_story(client)
    first = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": {"genre": "科幻"}, "expected_version": 1},
    )
    stale = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": {"genre": "悬疑"}, "expected_version": 1},
    )
    current = client.get(f"/api/v1/stories/{story['id']}/artifacts/concept")

    assert first.status_code == 200
    assert stale.status_code == 409
    assert current.json()["payload"] == {"genre": "科幻"}
    assert current.json()["version"] == 1


def test_model_failure_returns_an_error_without_changing_saved_concept(client):
    story = create_story(client)
    saved = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": {"genre": "科幻"}, "expected_version": 1},
    )
    failed = client.post(
        f"/api/v1/stories/{story['id']}/generations",
        json={"action": "generate_concept", "parameters": {"force_failure": True}},
    )
    current = client.get(f"/api/v1/stories/{story['id']}/artifacts/concept")

    assert saved.status_code == 200
    assert failed.status_code == 502
    assert failed.json()["detail"]["code"] == "model_unavailable"
    assert current.json()["payload"] == {"genre": "科幻"}