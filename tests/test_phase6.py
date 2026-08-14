"""Phase 6 tests: prose versions, sequential generation, deltas, consistency."""
import json

from app.infrastructure.fake_adapter import FakeModelAdapter

SCENE_PLAN_JSON = json.dumps([
    {"title": "场景甲", "location": "旧港", "time": "深夜", "pov": "林墨", "character_goals": "接触样本", "conflict": "匿名委托", "key_events": "发现编号", "scene_result": "接下委托", "chapter_goal_relation": "建立目标"},
    {"title": "场景乙", "location": "档案室", "time": "凌晨", "pov": "林墨", "character_goals": "寻找档案", "conflict": "页码替换", "key_events": "发现篡改", "scene_result": "确认人为", "chapter_goal_relation": "推进调查"},
], ensure_ascii=False)

PROSE_TEXT = "夜色沉了下来。林墨推开鉴定所的后门，一张没有署名的纸条静静躺在门槛上。"


def _setup_chapter_with_scenes(client, monkeypatch, title="Phase6 流程"):
    """Walk a story to chapter-planning and generate a scene plan with beats (2 chapters)."""
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {"deepseek": FakeModelAdapter('{"chapters":[{"title":"第一章","goal":"g","summary":"s","main_characters":["林墨"],"arc_role":"主线"},{"title":"第二章","goal":"g2"}]}')})
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(SCENE_PLAN_JSON)})
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(PROSE_TEXT)})
    created = client.post("/api/v1/works", json={"title": title}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "记忆鉴定师调查失踪案。", "expected_version": created["version"]})
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    chapters = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"}).json()["chapters"]
    chapter = chapters[0]
    scenes = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"}).json()["scenes"]
    return story_id, chapter, scenes


def test_generate_scene_auto_applies_prose(client, monkeypatch):
    """Generated prose is auto-applied (author-approved auto-accept); versions are preserved."""
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    response = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    assert response.status_code == 200
    produced = response.json()["prose_versions"]
    assert produced, "应生成至少一个 Beat 正文"
    assert all(p["status"] == "applied" for p in produced)
    assert all(p["applied_by"] == "ai" for p in produced)
    assert produced[0]["markdown"] == PROSE_TEXT
    # Beat is applied immediately after generation.
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    beat = context["scenes"][0]["beats"][0]
    assert beat["status"] == "applied"
    assert beat["latest_prose"]["status"] == "applied"


def test_apply_beat_prose_is_append_only(client, monkeypatch):
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    beat = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()["scenes"][0]["beats"][0]
    applied = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose-versions", json={"markdown": "作者手写正文。", "applied_by": "author", "expected_version": beat["version"]})
    assert applied.status_code == 200
    data = applied.json()
    assert data["status"] == "applied"
    assert data["applied_by"] == "author"
    assert data["version"] == 1
    # Append-only: second apply creates version 2, never overwrites.
    second = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose-versions", json={"markdown": "修订后正文。", "applied_by": "author", "expected_version": beat["version"] + 1})
    assert second.status_code == 200
    assert second.json()["version"] == 2
    assert second.json()["parent_id"] == data["id"]
    # Stale version -> 409
    conflict = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose-versions", json={"markdown": "冲突。", "applied_by": "author", "expected_version": beat["version"]})
    assert conflict.status_code == 409
    # History preserved
    prose = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose")
    assert len(prose.json()) == 2
    assert [p["version"] for p in prose.json()] == [1, 2]


def test_generate_chapter_remaining_completes_chapter(client, monkeypatch):
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    response = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_chapter_remaining"})
    assert response.status_code == 200
    produced = response.json()["prose_versions"]
    # Every beat across every scene gets a candidate version.
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    total_beats = sum(len(s["beats"]) for s in context["scenes"])
    assert len(produced) == total_beats


def test_regenerate_beat_creates_new_version_without_overwrite(client, monkeypatch):
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    beat = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()["scenes"][0]["beats"][0]
    first = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"}).json()["prose_versions"]
    regenerated = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "regenerate_beat", "beat_id": beat["id"]})
    assert regenerated.status_code == 200
    pv = regenerated.json()["prose_version"]
    assert pv["version"] == 2
    assert pv["status"] == "applied"
    assert pv["parent_id"] == first[0]["id"]
    # Both versions remain readable
    prose = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose").json()
    assert len(prose) == 2
    assert [p["status"] for p in prose] == ["applied", "applied"]


def test_generate_single_beat_is_idempotent_and_per_beat(client, monkeypatch):
    """generate_beat generates exactly one beat; repeating is idempotent (no duplicate prose)."""
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    beats = context["scenes"][0]["beats"]
    assert len(beats) >= 2
    first = beats[0]
    # Generate only the FIRST beat.
    r = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_beat", "beat_id": first["id"]})
    assert r.status_code == 200, r.text
    pv = r.json()["prose_version"]
    assert pv["beat_id"] == first["id"]
    assert pv["status"] == "applied"
    assert pv["applied_by"] == "ai"
    # The second beat is still not generated.
    context2 = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    beats2 = context2["scenes"][0]["beats"]
    assert beats2[0]["status"] == "applied"
    assert beats2[0]["latest_prose"]["markdown"] == PROSE_TEXT
    assert beats2[1]["status"] in ("available", "planned")
    assert not beats2[1].get("latest_prose")
    # Repeating the same beat is idempotent: returns the SAME prose version, no new version.
    r2 = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_beat", "beat_id": first["id"]})
    assert r2.status_code == 200
    assert r2.json()["prose_version"]["id"] == pv["id"]
    prose = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{first['id']}/prose").json()
    assert len(prose) == 1
    # Missing beat_id -> 422.
    r3 = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_beat"})
    assert r3.status_code == 422


def test_consistency_check_records_issues(client, monkeypatch):
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    # Generate with a very short prose to trigger the "too short" rule.
    short = FakeModelAdapter("短。")
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": short})
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    issues = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/issues").json()
    assert any(i["rule"] == "prose_too_short" for i in issues)


def test_confirm_chapter_delta_activates_next_chapter(client, monkeypatch):
    raw = '{"chapters":[{"title":"第一章","goal":"g1"},{"title":"第二章","goal":"g2"}]}'
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {"deepseek": FakeModelAdapter(raw)})
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(SCENE_PLAN_JSON)})
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(PROSE_TEXT)})
    created = client.post("/api/v1/works", json={"title": "确认章节"}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "测试创意", "expected_version": created["version"]})
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    chapters = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"}).json()["chapters"]
    chapter = next(c for c in chapters if c["access_status"] == "active")
    locked = next(c for c in chapters if c["access_status"] == "locked")
    scenes = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"}).json()["scenes"]
    # Apply every beat in the chapter so the chapter can be completed.
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    for scene in context["scenes"]:
        for beat in scene["beats"]:
            r = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose-versions", json={"markdown": "正文内容。", "applied_by": "author", "expected_version": beat["version"]})
            assert r.status_code == 200, r.text
    # Confirm chapter delta
    confirmed = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/deltas/confirm", json={})
    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["status"] == "confirmed"
    assert body["delta"]["scope_type"] == "chapter"
    assert body["next_chapter"]["access_status"] == "active"
    # Old chapter completed, next chapter active
    assert body["chapter"]["access_status"] == "completed"
    context2 = client.get(f"/api/v1/stories/{story_id}/chapters/{locked['id']}/context").json()
    assert context2["chapter"]["access_status"] == "active"
    # Living state records the confirmed delta as a NEW version (v2), with timeline events projected.
    blueprint = client.get(f"/api/v1/stories/{story_id}/blueprint").json()
    living_artifact = blueprint["living_state"]
    assert living_artifact["version"] == 2
    living = living_artifact["payload"]
    assert living["last_confirmed_chapter"] == 1
    assert len(living["confirmed_deltas"]) == 1
    timeline_entries = living["domains"]["timeline"]["state"]["entries"]
    assert any(e["name"].startswith("第 1 章") for e in timeline_entries)
    # Version-history endpoint returns both versions, newest first.
    history = client.get(f"/api/v1/stories/{story_id}/living-state/history").json()
    assert [h["version"] for h in history] == [2, 1]
    # Story stage advanced to writing
    work = client.get(f"/api/v1/works/{story_id}").json()
    assert work["stage"] == "writing"


def test_living_state_versions_increment_per_confirmed_chapter(client, monkeypatch):
    """Each confirmed chapter creates a new Living State version with projected timeline events."""
    raw = '{"chapters":[{"title":"第一章","goal":"g1"},{"title":"第二章","goal":"g2"}]}'
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {"deepseek": FakeModelAdapter(raw)})
    monkeypatch.setattr("app.planning.workspace_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(SCENE_PLAN_JSON)})
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(PROSE_TEXT)})
    created = client.post("/api/v1/works", json={"title": "版本递增"}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "测试创意", "expected_version": created["version"]})
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    chapters = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"}).json()["chapters"]
    for chapter in chapters:
        client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"})
        context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
        for scene in context["scenes"]:
            for beat in scene["beats"]:
                r = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/beats/{beat['id']}/prose-versions", json={"markdown": "正文内容。", "applied_by": "author", "expected_version": beat["version"]})
                assert r.status_code == 200, r.text
        confirmed = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/deltas/confirm", json={})
        assert confirmed.status_code == 200, confirmed.text
    # Living State advanced once per confirmed chapter: v1(initial) -> v2 -> v3.
    blueprint = client.get(f"/api/v1/stories/{story_id}/blueprint").json()
    living = blueprint["living_state"]
    assert living["version"] == 3
    assert living["payload"]["last_confirmed_chapter"] == 2
    assert len(living["payload"]["confirmed_deltas"]) == 2
    # History endpoint: newest first, each version carries projected domains.
    history = client.get(f"/api/v1/stories/{story_id}/living-state/history").json()
    assert [h["version"] for h in history] == [3, 2, 1]
    assert all(h["payload"]["domains"] for h in history)
    names = [e["name"] for e in history[0]["payload"]["domains"]["timeline"]["state"]["entries"]]
    assert any(n.startswith("第 1 章") for n in names)
    assert any(n.startswith("第 2 章") for n in names)


def test_story_reader_returns_continuous_prose(client, monkeypatch):
    """Reading mode returns every chapter with scenes and applied beat prose."""
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    # Generate prose for the whole scene (auto-applied).
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    # Reader endpoint: chapter 1 has applied prose, chapter 2 has none yet.
    reader = client.get(f"/api/v1/stories/{story_id}/read")
    assert reader.status_code == 200
    body = reader.json()
    assert body["story"]["id"] == story_id
    assert len(body["chapters"]) >= 2
    ch1 = body["chapters"][0]
    assert ch1["access_status"] in ("active", "completed")
    # Only beats with applied prose appear; scene order preserved.
    scene0 = ch1["scenes"][0]
    assert scene0["beats"], "first scene should carry generated prose"
    assert all(b["markdown"] for b in scene0["beats"])
    assert all(b["beat_name"] for b in scene0["beats"])
    # Second chapter has no prose yet -> scenes empty of beats.
    ch2 = body["chapters"][1]
    assert all(not s["beats"] for s in ch2["scenes"])


def test_confirm_delta_rejected_when_chapter_incomplete(client, monkeypatch):
    """Confirming a chapter with unwritten scenes/beats returns 409 (integrity gate)."""
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    # Only generate prose for the FIRST scene; later scenes stay unwritten.
    scene = scenes[0]
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    # Confirm must be rejected because other scenes' beats have no applied prose.
    r = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/deltas/confirm", json={})
    assert r.status_code == 409
    assert "尚未全部完成" in r.json()["detail"]
    # Chapter remains active.
    ch = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}").json()
    assert ch["access_status"] == "active"


def test_backfill_completes_incomplete_chapter(client, monkeypatch):
    """Backfill writes missing beat prose (using the chapter's entry snapshot)."""
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    scene = scenes[0]
    # Generate only the first scene; the chapter stays incomplete.
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    # Backfill the whole chapter.
    r = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/backfill", json={"action": "generate_scene"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "succeeded"
    assert len(body["prose_versions"]) > 0
    # Every beat now has applied prose.
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    total = 0
    written = 0
    for sc in context["scenes"]:
        for b in sc["beats"]:
            total += 1
            if b.get("latest_prose") and b["latest_prose"]["status"] == "applied":
                written += 1
    assert written == total, f"expected {total} applied beats, got {written}"
    # The chapter can now be confirmed.
    confirm = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/deltas/confirm", json={})
    assert confirm.status_code == 200


def test_mark_subsequent_stale_after_historical_change(client, monkeypatch, tmp_path):
    """Changing an earlier chapter marks later chapter snapshots stale."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.infrastructure.database import Base
    from app.planning.models import StateSnapshot, Chapter as ChapterModel
    from app.planning.writing_service import mark_subsequent_stale

    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    # Ensure the later chapter's snapshot exists via the API (GET context builds it).
    chapters = client.get(f"/api/v1/stories/{story_id}/chapters").json()
    locked = next(c for c in chapters if c["access_status"] == "locked")
    client.get(f"/api/v1/stories/{story_id}/chapters/{locked['id']}/context")
    # The client fixture used its own engine; build an independent one on the same file.
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as db:
        # Later chapter's snapshot exists; flip it stale via service.
        later_chapters = db.query(ChapterModel).filter(ChapterModel.story_id == story_id, ChapterModel.ordinal > chapter["ordinal"]).all()
        assert later_chapters, "应存在后续章节"
        count = mark_subsequent_stale(db, story_id, chapter["ordinal"])
        assert count == len(later_chapters)
        for later in later_chapters:
            snapshot = db.query(StateSnapshot).filter(StateSnapshot.chapter_id == later.id).first()
            if snapshot is not None:
                assert snapshot.status == "stale"
            assert "重算" in (later.stale_reason or "")


# ---------------------------------------------------------------------------
# Phase 6 enhancement: AI-driven delta extraction, scene summary, consistency
# ---------------------------------------------------------------------------

class DispatchAdapter(FakeModelAdapter):
    """Returns a canned response per model action (action-aware fake)."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[dict] = []

    def complete(self, messages, *, temperature=0.7, reasoning_strength="medium", json_mode=False, max_tokens=4096, action="chat"):
        self.calls.append({"action": action, "messages": messages})
        return self.responses.get(action, self.responses.get("default", PROSE_TEXT))


EMPTY_EXTRACT = '{"character_changes":[],"world_changes":[],"timeline_changes":[]}'


def _ai_phase6_adapter(scene_summary="林墨在旧港接下匿名委托，开始追查样本来源。", findings="[]"):
    return DispatchAdapter({
        "generate_scene": PROSE_TEXT,
        "extract_delta": EMPTY_EXTRACT,
        "consistency_check": findings,
        "scene_summary": scene_summary,
    })


def test_ai_delta_extraction_derives_changes(client, monkeypatch):
    """AI extraction returns character/world/timeline changes that land in the delta."""
    changes_json = json.dumps({
        "character_changes": [{"name": "林墨", "fields": {"status": "接下匿名委托"}}],
        "world_changes": [{"name": "鉴定所", "fields": {"found": "无署名纸条"}}],
        "timeline_changes": [{"event": "发现纸条", "scene": "场景甲", "note": "开端"}],
    }, ensure_ascii=False)
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    adapter = DispatchAdapter({
        "generate_scene": PROSE_TEXT,
        "extract_delta": changes_json,
        "consistency_check": "[]",
        "scene_summary": "摘要",
    })
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": adapter})
    scene = scenes[0]
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    deltas = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/deltas").json()
    beat_deltas = [d for d in deltas if d["scope_type"] == "beat"]
    assert beat_deltas
    changes = beat_deltas[0]["changes"]
    assert changes["character_changes"][0]["name"] == "林墨"
    assert changes["character_changes"][0]["fields"]["status"] == "接下匿名委托"
    assert changes["world_changes"][0]["name"] == "鉴定所"
    assert changes["timeline_changes"][0]["event"] == "发现纸条"


def test_scene_completion_generates_scene_summary(client, monkeypatch):
    """A completed scene gets an AI scene summary, exposed in context + reader."""
    summary_text = "林墨在旧港接下匿名委托，开始追查样本来源。"
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": _ai_phase6_adapter(scene_summary=summary_text)})
    scene = scenes[0]
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    # Scene completed and carries a summary.
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    scene0 = context["scenes"][0]
    assert scene0["status"] == "completed"
    assert scene0["summary"] == summary_text
    # Reader mode exposes the summary too.
    reader = client.get(f"/api/v1/stories/{story_id}/read").json()
    assert reader["chapters"][0]["scenes"][0]["summary"] == summary_text


def test_ai_consistency_check_records_model_findings(client, monkeypatch):
    """AI consistency findings are persisted as issues alongside deterministic rules."""
    findings = json.dumps([{"rule": "timeline_conflict", "severity": "error", "evidence": "正文事件与快照时间线矛盾"}], ensure_ascii=False)
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": _ai_phase6_adapter(findings=findings)})
    scene = scenes[0]
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_scene"})
    issues = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/issues").json()
    assert any(i["rule"] == "timeline_conflict" and i["severity"] == "error" for i in issues)


def test_later_scene_prompt_includes_prior_scene_summary(client, monkeypatch):
    """Scene 2's generation prompt includes scene 1's summary for continuity."""
    summary_text = "前置场景摘要内容"
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    adapter = _ai_phase6_adapter(scene_summary=summary_text)
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": adapter})
    client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/generations", json={"action": "generate_chapter_remaining"})
    gen_calls = [c for c in adapter.calls if c["action"] == "generate_scene"]
    assert len(gen_calls) >= 2, "章节应包含至少两个场景的生成调用"
    joined = "\n".join(str(c["messages"]) for c in gen_calls[1:])
    assert summary_text in joined


def test_generate_beat_by_beat_completes_scene_with_summary(client, monkeypatch):
    """UI 逐个 generate_beat 生成完整场景后：场景完成且生成摘要。"""
    summary_text = "逐个节拍生成后的场景摘要"
    story_id, chapter, scenes = _setup_chapter_with_scenes(client, monkeypatch)
    monkeypatch.setattr("app.planning.writing_service.build_adapters", lambda: {"deepseek": _ai_phase6_adapter(scene_summary=summary_text)})
    scene = scenes[0]
    context = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    beats = context["scenes"][0]["beats"]
    # 逐个 generate_beat（模拟工作台 UI 的逐个生成流程）。
    for beat in beats:
        r = client.post(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_beat", "beat_id": beat["id"]})
        assert r.status_code == 200, r.text
    # 场景完成且摘要已生成。
    context2 = client.get(f"/api/v1/stories/{story_id}/chapters/{chapter['id']}/context").json()
    scene0 = context2["scenes"][0]
    assert scene0["status"] == "completed"
    assert scene0["summary"] == summary_text

