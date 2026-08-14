"""API v1 route aggregation."""
import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.config import settings
from app.infrastructure.model_adapter import configured_model_specs
from app.works.schemas import AIConfigResponse, AIConfigUpdate, IdeaUpdate, ModelResponse, TitleUpdate, WorkCreate, WorkResponse
from app.works.service import create_story, get_ai_config, get_story_or_404, list_stories, soft_delete_story, update_ai_config, update_idea, update_title
from app.works.concept_schemas import ConceptConfirm, ConceptGenerationRequest, ConceptUpdate
from app.works.concept_service import confirm_concept, concept_response, generate_concept, latest_concept, update_concept
from app.works.blueprint_schemas import BlueprintConfirm, BlueprintGenerationRequest, BlueprintUpdate, artifact_response
from app.works.blueprint_service import confirm_blueprint, generate_blueprint, latest_blueprint, list_blueprint, list_living_state_history, update_blueprint
from app.planning.schemas import ChapterPlanGenerationRequest, ChapterPlanUpdate
from app.planning.service import chapter_response, generate_chapter_plan, get_chapter, list_chapters, update_chapter_plan
from app.planning.workspace_schemas import (
    BeatUpdate,
    ChapterDeltaConfirm,
    ChapterEventUpdate,
    ProseVersionCreate,
    ScenePlanGenerationRequest,
    SceneUpdate,
)
from app.planning.workspace_service import (
    build_state_snapshot,
    create_beat,
    create_event,
    create_scene,
    delete_beat,
    delete_event,
    delete_scene,
    event_response,
    generate_beat_plan,
    generate_scene_plan,
    get_chapter_context,
    scene_response,
    update_beat,
    update_event,
    update_scene,
)
from app.planning.writing_service import (
    apply_beat_prose,
    build_chapter_delta,
    confirm_chapter_delta,
    delta_response,
    generate_chapter_remaining,
    generate_scene,
    generate_single_beat,
    issue_response,
    list_prose,
    mark_subsequent_stale,
    prose_response,
    regenerate_beat,
    run_consistency_check,
)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.get("/works", response_model=list[WorkResponse])
def get_works(db: Session = Depends(get_db)):
    return list_stories(db)


@router.post("/works", response_model=WorkResponse, status_code=status.HTTP_201_CREATED)
def post_work(payload: WorkCreate, db: Session = Depends(get_db)):
    return create_story(db, payload)


@router.get("/works/{story_id}", response_model=WorkResponse)
def get_work(story_id: str, db: Session = Depends(get_db)):
    return get_story_or_404(db, story_id)


@router.delete("/works/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work(story_id: str, response: Response, db: Session = Depends(get_db)):
    soft_delete_story(db, story_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@router.put("/stories/{story_id}/idea", response_model=WorkResponse)
def put_idea(story_id: str, payload: IdeaUpdate, db: Session = Depends(get_db)):
    return update_idea(db, story_id, payload)


@router.put("/stories/{story_id}/title", response_model=WorkResponse)
def put_story_title(story_id: str, payload: TitleUpdate, db: Session = Depends(get_db)):
    return update_title(db, story_id, payload)


@router.get("/stories/{story_id}/ai-config", response_model=AIConfigResponse)
def get_story_ai_config(story_id: str, db: Session = Depends(get_db)):
    return get_ai_config(db, story_id)


@router.put("/stories/{story_id}/ai-config", response_model=AIConfigResponse)
def put_story_ai_config(story_id: str, payload: AIConfigUpdate, db: Session = Depends(get_db)):
    return update_ai_config(db, story_id, payload)


@router.get("/models", response_model=list[ModelResponse])
def get_models():
    return [ModelResponse(provider=s.provider, name=s.name, model=s.model, supports_json=s.supports_json, configured=bool(os.getenv(s.api_key_env) or getattr(settings, s.api_key_env.lower(), ""))) for s in configured_model_specs()]


@router.get("/stories/{story_id}/concept")
def get_concept(story_id: str, db: Session = Depends(get_db)):
    get_story_or_404(db, story_id)
    artifact = latest_concept(db, story_id)
    if artifact is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return concept_response(artifact)


@router.post("/stories/{story_id}/generations")
def post_generation(story_id: str, payload: ConceptGenerationRequest, db: Session = Depends(get_db)):
    artifact, task = generate_concept(db, story_id, payload)
    return {"task_id": task.id, "artifact": concept_response(artifact), "status": task.status}


@router.put("/stories/{story_id}/concept")
def put_concept(story_id: str, payload: ConceptUpdate, db: Session = Depends(get_db)):
    return concept_response(update_concept(db, story_id, payload))


@router.post("/stories/{story_id}/concept/confirm")
def post_concept_confirm(story_id: str, payload: ConceptConfirm, db: Session = Depends(get_db)):
    return concept_response(confirm_concept(db, story_id, payload))


@router.get("/stories/{story_id}/blueprint")
def get_blueprint(story_id: str, db: Session = Depends(get_db)):
    artifacts = list_blueprint(db, story_id)
    return {kind: artifact_response(artifact) if artifact else None for kind, artifact in artifacts.items()}


@router.get("/stories/{story_id}/living-state/history")
def get_living_state_history(story_id: str, db: Session = Depends(get_db)):
    """All Living State versions (newest first) for the version-history modal."""
    return [artifact_response(artifact) for artifact in list_living_state_history(db, story_id)]


@router.get("/stories/{story_id}/blueprint/{kind}")
def get_blueprint_kind(story_id: str, kind: str, db: Session = Depends(get_db)):
    get_story_or_404(db, story_id)
    artifact = latest_blueprint(db, story_id, kind)
    if artifact is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return artifact_response(artifact)


@router.post("/stories/{story_id}/blueprint/generations")
def post_blueprint_generation(story_id: str, payload: BlueprintGenerationRequest, db: Session = Depends(get_db)):
    artifacts = generate_blueprint(db, story_id, payload)
    return {"status": "succeeded", "artifacts": [artifact_response(artifact) for artifact in artifacts]}


@router.put("/stories/{story_id}/blueprint/{kind}")
def put_blueprint_kind(story_id: str, kind: str, payload: BlueprintUpdate, db: Session = Depends(get_db)):
    return artifact_response(update_blueprint(db, story_id, kind, payload))


@router.post("/stories/{story_id}/blueprint/confirm")
def post_blueprint_confirm(story_id: str, payload: BlueprintConfirm, db: Session = Depends(get_db)):
    return {"status": "confirmed", "artifacts": [artifact_response(artifact) for artifact in confirm_blueprint(db, story_id, payload)]}


@router.get("/stories/{story_id}/chapters")
def get_story_chapters(story_id: str, db: Session = Depends(get_db)):
    return [chapter_response(chapter) for chapter in list_chapters(db, story_id)]


@router.post("/stories/{story_id}/chapter-plan")
def post_chapter_plan(story_id: str, payload: ChapterPlanGenerationRequest, db: Session = Depends(get_db)):
    return {"status": "succeeded", "chapters": [chapter_response(chapter) for chapter in generate_chapter_plan(db, story_id, payload)]}


@router.get("/stories/{story_id}/chapters/{chapter_id}")
def get_story_chapter(story_id: str, chapter_id: str, db: Session = Depends(get_db)):
    return chapter_response(get_chapter(db, story_id, chapter_id))


@router.put("/stories/{story_id}/chapters/{chapter_id}/plan")
def put_story_chapter_plan(story_id: str, chapter_id: str, payload: ChapterPlanUpdate, db: Session = Depends(get_db)):
    return chapter_response(update_chapter_plan(db, story_id, chapter_id, payload))


# --- Phase 5: Chapter Workspace (context / events / scenes / beats) ---

@router.get("/stories/{story_id}/chapters/{chapter_id}/context")
def get_story_chapter_context(story_id: str, chapter_id: str, db: Session = Depends(get_db)):
    return get_chapter_context(db, story_id, chapter_id)


@router.post("/stories/{story_id}/chapters/{chapter_id}/generations")
def post_chapter_workspace_generation(story_id: str, chapter_id: str, payload: ScenePlanGenerationRequest, db: Session = Depends(get_db)):
    if payload.action == "generate_scene_plan":
        scenes = generate_scene_plan(db, story_id, chapter_id, payload)
        return {"status": "succeeded", "scenes": [scene_response(s, []) for s in scenes]}
    if payload.action == "generate_chapter_remaining":
        produced = generate_chapter_remaining(db, story_id, chapter_id, payload)
        return {"status": "succeeded", "prose_versions": [prose_response(p) for p in produced]}
    # generate_beat_plan requires a scene id — handled by scene-scoped endpoint below
    raise HTTPException(status_code=422, detail="generate_beat_plan requires scene_id; use /scenes/{scene_id}/generations")


@router.post("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}/generations")
def post_scene_beat_generation(story_id: str, chapter_id: str, scene_id: str, payload: ScenePlanGenerationRequest, db: Session = Depends(get_db)):
    if payload.action == "generate_beat_plan":
        beats = generate_beat_plan(db, story_id, chapter_id, scene_id, payload)
        return {"status": "succeeded", "beats": [{"id": b.id, "scene_id": b.scene_id, "ordinal": b.ordinal, "name": b.name, "instruction": b.instruction, "status": b.status, "version": b.version} for b in beats]}
    if payload.action == "generate_scene":
        produced = generate_scene(db, story_id, chapter_id, scene_id, payload)
        return {"status": "succeeded", "prose_versions": [prose_response(p) for p in produced]}
    if payload.action == "generate_beat":
        if not payload.beat_id:
            raise HTTPException(status_code=422, detail="generate_beat requires beat_id")
        pv = generate_single_beat(db, story_id, chapter_id, scene_id, payload.beat_id, payload)
        return {"status": "succeeded", "prose_version": prose_response(pv)}
    if payload.action == "regenerate_beat":
        if not payload.beat_id:
            raise HTTPException(status_code=422, detail="regenerate_beat requires beat_id")
        pv = regenerate_beat(db, story_id, chapter_id, scene_id, payload.beat_id, payload)
        return {"status": "succeeded", "prose_version": prose_response(pv)}
    raise HTTPException(status_code=422, detail="Unsupported action for scene generation")


# --- Phase 6: prose versions, deltas, consistency ---

@router.get("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}/beats/{beat_id}/prose")
def get_beat_prose(story_id: str, chapter_id: str, scene_id: str, beat_id: str, db: Session = Depends(get_db)):
    return [prose_response(pv) for pv in list_prose(db, beat_id)]


@router.post("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}/beats/{beat_id}/prose-versions")
def post_beat_prose(story_id: str, chapter_id: str, scene_id: str, beat_id: str, payload: ProseVersionCreate, db: Session = Depends(get_db)):
    return prose_response(apply_beat_prose(db, story_id, chapter_id, scene_id, beat_id, payload))


@router.get("/stories/{story_id}/chapters/{chapter_id}/deltas")
def get_chapter_deltas(story_id: str, chapter_id: str, db: Session = Depends(get_db)):
    from app.planning.models import StateDelta
    from sqlalchemy import select
    deltas = list(db.scalars(select(StateDelta).where(StateDelta.chapter_id == chapter_id).order_by(StateDelta.created_at)))
    return [delta_response(d) for d in deltas]


@router.post("/stories/{story_id}/chapters/{chapter_id}/deltas/confirm")
def post_chapter_delta_confirm(story_id: str, chapter_id: str, payload: ChapterDeltaConfirm, db: Session = Depends(get_db)):
    return confirm_chapter_delta(db, story_id, chapter_id, payload.expected_delta_id)


@router.get("/stories/{story_id}/chapters/{chapter_id}/issues")
def get_chapter_issues(story_id: str, chapter_id: str, db: Session = Depends(get_db)):
    from app.planning.models import ConsistencyIssue
    from sqlalchemy import select
    issues = list(db.scalars(select(ConsistencyIssue).where(ConsistencyIssue.chapter_id == chapter_id).order_by(ConsistencyIssue.created_at)))
    return [issue_response(i) for i in issues]


# TODO: Phase 2 — idea / concept
# TODO: Phase 3 — blueprint / entities
# TODO: Phase 4 — chapter plan
# TODO: Phase 5 — workspace: context, scenes, beats
# TODO: Phase 6 — prose generation, delta, consistency


@router.post("/stories/{story_id}/chapters/{chapter_id}/events")
def post_chapter_event(story_id: str, chapter_id: str, db: Session = Depends(get_db)):
    return event_response(create_event(db, story_id, chapter_id))


@router.put("/stories/{story_id}/chapters/{chapter_id}/events/{event_id}")
def put_chapter_event(story_id: str, chapter_id: str, event_id: str, payload: ChapterEventUpdate, db: Session = Depends(get_db)):
    return event_response(update_event(db, story_id, chapter_id, event_id, payload))


@router.delete("/stories/{story_id}/chapters/{chapter_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter_event(story_id: str, chapter_id: str, event_id: str, response: Response, db: Session = Depends(get_db)):
    delete_event(db, story_id, chapter_id, event_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@router.post("/stories/{story_id}/chapters/{chapter_id}/scenes")
def post_chapter_scene(story_id: str, chapter_id: str, db: Session = Depends(get_db)):
    return scene_response(create_scene(db, story_id, chapter_id))


@router.put("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}")
def put_chapter_scene(story_id: str, chapter_id: str, scene_id: str, payload: SceneUpdate, db: Session = Depends(get_db)):
    return scene_response(update_scene(db, story_id, chapter_id, scene_id, payload))


@router.delete("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter_scene(story_id: str, chapter_id: str, scene_id: str, response: Response, db: Session = Depends(get_db)):
    delete_scene(db, story_id, chapter_id, scene_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@router.post("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}/beats")
def post_scene_beat(story_id: str, chapter_id: str, scene_id: str, db: Session = Depends(get_db)):
    beat = create_beat(db, story_id, chapter_id, scene_id)
    return {"id": beat.id, "scene_id": beat.scene_id, "ordinal": beat.ordinal, "name": beat.name, "instruction": beat.instruction, "status": beat.status, "version": beat.version}


@router.put("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}/beats/{beat_id}")
def put_scene_beat(story_id: str, chapter_id: str, scene_id: str, beat_id: str, payload: BeatUpdate, db: Session = Depends(get_db)):
    beat = update_beat(db, story_id, chapter_id, scene_id, beat_id, payload)
    return {"id": beat.id, "scene_id": beat.scene_id, "ordinal": beat.ordinal, "name": beat.name, "instruction": beat.instruction, "status": beat.status, "version": beat.version}


@router.delete("/stories/{story_id}/chapters/{chapter_id}/scenes/{scene_id}/beats/{beat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene_beat(story_id: str, chapter_id: str, scene_id: str, beat_id: str, response: Response, db: Session = Depends(get_db)):
    delete_beat(db, story_id, chapter_id, scene_id, beat_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


# TODO: Phase 2 — idea / concept
# TODO: Phase 3 — blueprint / entities
# TODO: Phase 4 — chapter plan
# TODO: Phase 5 — workspace: context, scenes, beats
# TODO: Phase 6 — prose generation, delta, consistency
