"""API v1 route aggregation."""
import os

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.config import settings
from app.infrastructure.model_adapter import configured_model_specs
from app.works.schemas import AIConfigResponse, AIConfigUpdate, IdeaUpdate, ModelResponse, WorkCreate, WorkResponse
from app.works.service import create_story, get_ai_config, get_story_or_404, list_stories, soft_delete_story, update_ai_config, update_idea
from app.works.concept_schemas import ConceptConfirm, ConceptGenerationRequest, ConceptUpdate
from app.works.concept_service import confirm_concept, concept_response, generate_concept, latest_concept, update_concept
from app.works.blueprint_schemas import BlueprintConfirm, BlueprintGenerationRequest, BlueprintUpdate, artifact_response
from app.works.blueprint_service import confirm_blueprint, generate_blueprint, latest_blueprint, list_blueprint, update_blueprint
from app.planning.schemas import ChapterPlanGenerationRequest, ChapterPlanUpdate
from app.planning.service import chapter_response, generate_chapter_plan, get_chapter, list_chapters, update_chapter_plan

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


# TODO: Phase 2 — idea / concept
# TODO: Phase 3 — blueprint / entities
# TODO: Phase 4 — chapter plan
# TODO: Phase 5 — workspace: context, scenes, beats
# TODO: Phase 6 — prose generation, delta, consistency
