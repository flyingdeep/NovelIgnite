def create_confirmed_story(client):
    story = client.post("/api/v1/stories", json={"idea": "鉴定师在记忆黑市追寻自己的过去。"}).json()
    response = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/concept",
        json={"payload": {"genre": "科幻悬疑"}, "expected_version": 1, "status": "confirmed"},
    )
    assert response.status_code == 200
    return story


def test_author_can_confirm_separate_blueprint_baseline_and_living_state(client):
    story = create_confirmed_story(client)
    bible = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/bible",
        json={"payload": {"characters": [{"name": "林墨"}], "world": {"rule": "记忆可交易"}}, "expected_version": 1},
    )
    living = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/living_state",
        json={"payload": {"timeline": {"current": "故事开始"}}, "layer": "living", "expected_version": 1},
    )
    story_after = client.get(f"/api/v1/stories/{story['id']}")

    assert bible.status_code == 200
    assert bible.json()["layer"] == "baseline"
    assert living.status_code == 200
    assert living.json()["layer"] == "living"
    assert story_after.json()["status"] == "blueprint_review"


def test_blueprint_generation_is_a_candidate_until_author_explicitly_confirms_it(client):
    story = create_confirmed_story(client)
    candidate = client.post(
        f"/api/v1/stories/{story['id']}/generations",
        json={"action": "generate_blueprint"},
    )
    client.put(
        f"/api/v1/stories/{story['id']}/artifacts/bible",
        json={"payload": {"characters": [], "world": {}, "initial_timeline": []}, "expected_version": 1},
    )
    client.put(
        f"/api/v1/stories/{story['id']}/artifacts/arc",
        json={"payload": {"stages": []}, "expected_version": 1},
    )
    before_confirmation = client.get(f"/api/v1/stories/{story['id']}")
    confirmed = client.post(f"/api/v1/stories/{story['id']}/blueprint/confirm")

    assert candidate.status_code == 200
    assert candidate.json()["status"] == "succeeded"
    assert before_confirmation.json()["status"] == "blueprint_review"
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "blueprint_confirmed"


def test_entities_are_unique_per_story_and_can_lock_stable_data(client):
    story = create_confirmed_story(client)
    entity = client.post(
        f"/api/v1/stories/{story['id']}/entities",
        json={"type": "character", "name": "林墨", "canonical_data": {"occupation": "鉴定师"}, "lock_state": "locked"},
    )
    duplicate = client.post(
        f"/api/v1/stories/{story['id']}/entities",
        json={"type": "character", "name": "林墨", "canonical_data": {}},
    )

    assert entity.status_code == 201
    assert entity.json()["lock_state"] == "locked"
    assert duplicate.status_code == 409


def test_locked_entity_and_stale_entity_version_reject_edits(client):
    story = create_confirmed_story(client)
    entity = client.post(
        f"/api/v1/stories/{story['id']}/entities",
        json={"type": "character", "name": "林墨", "canonical_data": {"occupation": "鉴定师"}},
    ).json()
    locked = client.put(
        f"/api/v1/stories/{story['id']}/entities/{entity['id']}",
        json={"canonical_data": {"occupation": "调查员"}, "lock_state": "locked", "expected_version": 1},
    )
    blocked = client.put(
        f"/api/v1/stories/{story['id']}/entities/{entity['id']}",
        json={"canonical_data": {"occupation": "冒险家"}, "lock_state": "locked", "expected_version": 2},
    )

    assert locked.status_code == 200
    assert locked.json()["version"] == 2
    assert blocked.status_code == 409


def test_confirmed_state_entries_are_grouped_by_domain_and_preserve_source(client):
    story = create_confirmed_story(client)
    entity = client.post(
        f"/api/v1/stories/{story['id']}/entities",
        json={"type": "character", "name": "林墨", "canonical_data": {}},
    ).json()
    created = client.post(
        f"/api/v1/stories/{story['id']}/state-entries",
        json={
            "domain": "character",
            "subject_id": entity["id"],
            "path": "character.location",
            "value": "旧港鉴定所",
            "source_ref": {"artifact": "bible", "version": 1},
            "temporal_scope": {"effective": "current"},
            "certainty": "confirmed",
            "context_policy": "always",
        },
    )
    states = client.get(f"/api/v1/stories/{story['id']}/state-entries")

    assert created.status_code == 201
    assert states.status_code == 200
    assert states.json()["character"][0]["value"] == "旧港鉴定所"
    assert states.json()["character"][0]["source_ref"] == {"artifact": "bible", "version": 1}
    assert states.json()["world"] == []
    assert states.json()["timeline"] == []


def test_living_state_requires_explicit_confirmation_and_cannot_use_baseline_layer(client):
    story = create_confirmed_story(client)
    invalid_layer = client.put(
        f"/api/v1/stories/{story['id']}/artifacts/living_state",
        json={"payload": {}, "layer": "baseline", "expected_version": 1},
    )
    proposed_state = client.post(
        f"/api/v1/stories/{story['id']}/state-entries",
        json={
            "domain": "timeline",
            "subject_id": None,
            "path": "timeline.current",
            "value": "计划中的未来事件",
            "source_ref": {"plan": "chapter-1"},
            "temporal_scope": {"effective": "future"},
            "certainty": "proposed",
            "context_policy": "blocked",
        },
    )

    assert invalid_layer.status_code == 422
    assert proposed_state.status_code == 422