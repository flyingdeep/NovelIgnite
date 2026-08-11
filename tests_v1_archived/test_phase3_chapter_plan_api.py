def confirmed_blueprint(client):
    story = client.post("/api/v1/stories", json={"idea": "记忆鉴定师追查被拍卖的过去。"}).json()
    client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": {"genre": "科幻"}, "expected_version": 1, "status": "confirmed"},
    )
    client.put(
        f"/api/v1/stories/{story['id']}/artifacts/bible",
        json={"payload": {"characters": [], "world": {}, "initial_timeline": []}, "expected_version": 1},
    )
    client.put(
        f"/api/v1/stories/{story['id']}/artifacts/arc",
        json={"payload": {"stages": []}, "expected_version": 1},
    )
    assert client.post(f"/api/v1/stories/{story['id']}/blueprint/confirm").status_code == 200
    return story


def test_blueprint_creates_one_active_first_chapter_and_locked_outlines(client):
    story = confirmed_blueprint(client)
    created = client.post(f"/api/v1/stories/{story['id']}/chapter-plan", json={"chapter_count": 4})
    chapters = client.get(f"/api/v1/stories/{story['id']}/chapters")

    assert created.status_code == 201
    assert len(chapters.json()) == 4
    assert chapters.json()[0]["ordinal"] == 1
    assert chapters.json()[0]["plan_status"] == "fixed"
    assert chapters.json()[0]["access_status"] == "active"
    assert [chapter["access_status"] for chapter in chapters.json()[1:]] == ["locked", "locked", "locked"]


def test_locked_outline_is_versioned_but_fixed_active_chapter_cannot_be_edited_as_outline(client):
    story = confirmed_blueprint(client)
    chapters = client.post(f"/api/v1/stories/{story['id']}/chapter-plan", json={"chapter_count": 3}).json()
    locked = chapters[1]
    revised = client.put(
        f"/api/v1/chapters/{locked['id']}/outline",
        json={
            "title": "修订后的第二章",
            "summary": "后续章节雏形仍是计划，不是已发生事实。",
            "goal": "推进调查。",
            "main_characters": ["主角"],
            "arc_relation": "推进中段。",
            "expected_version": 1,
        },
    )
    fixed = client.put(
        f"/api/v1/chapters/{chapters[0]['id']}/outline",
        json={
            "title": "不允许覆盖首章",
            "summary": "x",
            "goal": "x",
            "expected_version": 1,
        },
    )

    assert revised.status_code == 200
    assert revised.json()["plan_status"] == "revised"
    assert revised.json()["version"] == 2
    assert fixed.status_code == 409


def test_chapter_plan_cannot_be_created_before_blueprint_confirmation(client):
    story = client.post("/api/v1/stories", json={"idea": "尚未确认的故事"}).json()
    response = client.post(f"/api/v1/stories/{story['id']}/chapter-plan", json={})
    assert response.status_code == 409


def test_workspace_rejects_locked_chapter_but_allows_unique_active_chapter(client):
    story = confirmed_blueprint(client)
    chapters = client.post(f"/api/v1/stories/{story['id']}/chapter-plan", json={"chapter_count": 3}).json()

    active = client.get(f"/api/v1/chapters/{chapters[0]['id']}/workspace")
    locked = client.get(f"/api/v1/chapters/{chapters[1]['id']}/workspace")

    assert active.status_code == 200
    assert active.json()["chapter"]["access_status"] == "active"
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "chapter_not_active"
