"""Phase 5 tests: Chapter Workspace context, snapshots, events, scenes, beats."""
import json

from app.infrastructure.fake_adapter import FakeModelAdapter

SCENE_PLAN_JSON = json.dumps([
    {"title": "深夜委托", "location": "旧港鉴定所", "time": "深夜", "pov": "林墨", "character_goals": "接触异常样本", "conflict": "匿名委托", "key_events": "发现样本编号", "scene_result": "主角接下委托", "chapter_goal_relation": "建立本章目标"},
    {"title": "档案室", "location": "档案室", "time": "凌晨", "pov": "林墨", "character_goals": "寻找事故档案", "conflict": "页码替换", "key_events": "发现记录被替换", "scene_result": "确认人为篡改", "chapter_goal_relation": "推进调查"},
    {"title": "邀请函", "location": "鉴定所", "time": "清晨前", "pov": "林墨", "character_goals": "决定是否赴约", "conflict": "是否信任线索", "key_events": "收到邀请函", "scene_result": "决定前往", "chapter_goal_relation": "收束本章"},
], ensure_ascii=False)


def _setup_chapter_plan(client, monkeypatch, title="Phase5 流程"):
    """Create a story and walk it to chapter-planning stage with an active chapter."""
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {"deepseek": FakeModelAdapter('{"chapters":[{"title":"第一章","goal":"g","summary":"s","main_characters":["林墨"],"arc_role":"主线"}]}')})
    created = client.post("/api/v1/works", json={"title": title}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "记忆鉴定师调查失踪案。", "expected_version": created["version"]})
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    generated = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"})
    assert generated.status_code == 200
    chapter = generated.json()["chapters"][0]
    assert chapter["access_status"] == "active"
    return story_id, chapter


def test_context_builds_snapshot_from_living_state(client, monkeypatch):
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {})
    story_id, chapter = _setup_chapter_plan(client, monkeypatch)
    response = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context")
    assert response.status_code == 200
    body = response.json()
    assert body["chapter"]["id"] == chapter["id"]
    snapshot = body["snapshot"]
    assert snapshot is not None
    assert snapshot["status"] == "valid"
    assert set(snapshot["state"].keys()) == {"characters", "world", "timeline"}
    assert snapshot["state_hash"]
    # Events and scenes start empty (author drives planning)
    assert body["events"] == []
    assert body["scenes"] == []


def test_chapter_event_edit_with_planned_and_actual_results(client, monkeypatch):
    story_id, chapter = _setup_chapter_plan(client, monkeypatch)
    created = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/events")
    assert created.status_code == 200
    event = created.json()
    assert event["ordinal"] == 1

    updated = client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/events/{event['id']}", json={
        "title": "发现样本",
        "related_characters": ["林墨"],
        "related_locations": ["鉴定所"],
        "goal": "确认样本来源",
        "planned_result": "样本编号与病历关联",
        "actual_result": "",
        "impact": "把线索指向下一场景",
        "arc_role": "推进调查",
        "expected_version": event["version"],
    })
    assert updated.status_code == 200
    data = updated.json()
    assert data["planned_result"] == "样本编号与病历关联"
    assert data["actual_result"] == ""  # separated from planned result
    assert data["version"] == event["version"] + 1

    # Optimistic lock: stale version -> 409
    conflict = client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/events/{event['id']}", json={"goal": "新目标", "expected_version": event["version"]})
    assert conflict.status_code == 409

    # Actual result can be filled later without touching planned
    filled = client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/events/{event['id']}", json={"actual_result": "确认记录被替换", "expected_version": data["version"]})
    assert filled.status_code == 200
    assert filled.json()["planned_result"] == "样本编号与病历关联"
    assert filled.json()["actual_result"] == "确认记录被替换"


def test_scene_plan_generation_with_ordering(client, monkeypatch):
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(SCENE_PLAN_JSON)})
    story_id, chapter = _setup_chapter_plan(client, monkeypatch)
    response = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"})
    assert response.status_code == 200
    scenes = response.json()["scenes"]
    assert len(scenes) == 3
    assert [s["ordinal"] for s in scenes] == [1, 2, 3]
    assert scenes[0]["status"] == "available"  # only smallest unfinished ordinal
    assert scenes[1]["status"] == "planned"
    assert scenes[2]["status"] == "planned"
    assert scenes[0]["title"] == "深夜委托"
    assert scenes[1]["conflict"] == "页码替换"


def test_beat_plan_generation_ordering(client, monkeypatch):
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(SCENE_PLAN_JSON)})
    story_id, chapter = _setup_chapter_plan(client, monkeypatch)
    scenes = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"}).json()["scenes"]
    scene_id = scenes[0]["id"]
    beats = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene_id}/generations", json={"action": "generate_beat_plan"}).json()["beats"]
    assert len(beats) >= 3
    assert beats[0]["status"] == "available"
    assert all(b["status"] == "planned" for b in beats[1:])
    # Beats appear inside chapter context
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    assert context["scenes"][0]["beats"][0]["name"] == beats[0]["name"]


def test_scene_beat_update_with_version_conflict(client, monkeypatch):
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(SCENE_PLAN_JSON)})
    story_id, chapter = _setup_chapter_plan(client, monkeypatch)
    scene = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"}).json()["scenes"][0]

    updated = client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}", json={"conflict": "阻力升级", "expected_version": scene["version"]})
    assert updated.status_code == 200
    assert updated.json()["conflict"] == "阻力升级"

    conflict = client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}", json={"conflict": "覆盖", "expected_version": scene["version"]})
    assert conflict.status_code == 409

    beat = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats").json()
    updated_beat = client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}", json={"name": "新节拍", "expected_version": beat["version"]})
    assert updated_beat.status_code == 200
    assert updated_beat.json()["name"] == "新节拍"
    assert client.put(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}", json={"name": "覆盖", "expected_version": beat["version"]}).status_code == 409


def test_locked_chapter_context_is_readonly(client, monkeypatch):
    """Only the active chapter can be planned; locked chapter edits return 409."""
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    # 不依赖真实模型：workspace 场景/节拍生成走确定性 fallback。
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {})
    raw = '{"chapters":[{"title":"第一章","goal":"g1"},{"title":"第二章","goal":"g2"}]}'
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {"deepseek": FakeModelAdapter(raw)})
    created = client.post("/api/v1/works", json={"title": "锁定章节"}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "测试创意", "expected_version": created["version"]})
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    chapters = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"}).json()["chapters"]
    active = next(c for c in chapters if c["access_status"] == "active")
    locked = next(c for c in chapters if c["access_status"] == "locked")

    # Locked chapter: context readable, edits rejected
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{locked['id']}/context")
    assert context.status_code == 200
    assert client.post(f"/api/v1/stories/{story_id}/chapters/{locked['id']}/events").status_code == 409
    assert client.post(f"/api/v1/stories/{story_id}/chapters/{locked['id']}/generations", json={"action": "generate_scene_plan"}).status_code == 409

    # Active chapter: scene plan editable
    assert client.post(f"/api/v1/stories/{story_id}/chapters/{active['id']}/generations", json={"action": "generate_scene_plan"}).status_code == 200


def test_event_delete_removes_from_context(client, monkeypatch):
    story_id, chapter = _setup_chapter_plan(client, monkeypatch)
    event = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/events").json()
    assert client.delete(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/events/{event['id']}").status_code == 204
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    assert context["events"] == []
