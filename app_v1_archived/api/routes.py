from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.config import get_settings
from app.infrastructure.database import get_session
from app.planning.schemas import ChapterCard, ChapterOutlineUpdate, ChapterPlanGenerate, ChapterWorkspaceResponse
from app.planning.service import ChapterPlanningService
from app.projects.schemas import (
    ArtifactResponse,
    ArtifactUpdate,
    BlueprintArtifactUpdate,
    EntityCreate,
    EntityResponse,
    EntityUpdate,
    GenerationCreate,
    GenerationResponse,
    ModelInfo,
    StateEntriesResponse,
    StateEntryCreate,
    StateEntryResponse,
    StoryCreate,
    StoryResponse,
)
from app.projects.service import (
    ConflictError,
    ModelGenerationError,
    NotFoundError,
    ProjectService,
    build_model_adapters,
)

router = APIRouter(prefix="/api/v1")


def get_service(session: Session = Depends(get_session)) -> ProjectService:
    settings = get_settings()
    return ProjectService(
        session,
        models=build_model_adapters(settings),
        default_provider=settings.model_provider,
    )


def get_planning_service(session: Session = Depends(get_session)) -> ChapterPlanningService:
    return ChapterPlanningService(session, get_service(session))


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "not_found"})


@router.get("/models", response_model=list[ModelInfo])
def list_models(service: ProjectService = Depends(get_service)) -> list[ModelInfo]:
    return service.list_models()


@router.post("/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(payload: StoryCreate, service: ProjectService = Depends(get_service)) -> StoryResponse:
    return service.create_story(payload.idea, payload.title)


@router.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: str, service: ProjectService = Depends(get_service)) -> StoryResponse:
    try:
        return service.get_story(story_id)
    except NotFoundError:
        raise not_found() from None


@router.post("/stories/{story_id}/generations", response_model=GenerationResponse)
def generate(story_id: str, payload: GenerationCreate, service: ProjectService = Depends(get_service)) -> GenerationResponse:
    try:
        if payload.action == "generate_blueprint":
            return service.generate_blueprint(story_id, payload.parameters)
        if payload.action == "generate_chapter_plan":
            return service.generate_chapter_plan(story_id, payload.parameters)
        return service.generate_concept(story_id, payload.parameters)
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "invalid_generation_state"}) from None
    except ModelGenerationError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "model_unavailable"}) from None


@router.get("/stories/{story_id}/generations/{task_id}", response_model=GenerationResponse)
def get_generation_task(
    story_id: str, task_id: str, service: ProjectService = Depends(get_service)
) -> GenerationResponse:
    try:
        return service.get_generation_task(story_id, task_id)
    except NotFoundError:
        raise not_found() from None


@router.put("/stories/{story_id}/artifacts/concept", response_model=ArtifactResponse)
def update_concept(story_id: str, payload: ArtifactUpdate, service: ProjectService = Depends(get_service)) -> ArtifactResponse:
    try:
        return service.update_concept(story_id, **payload.model_dump())
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "version_or_lock_conflict"}) from None


@router.get("/stories/{story_id}/artifacts/concept", response_model=ArtifactResponse)
def get_concept(story_id: str, service: ProjectService = Depends(get_service)) -> ArtifactResponse:
    try:
        return service.get_artifact(story_id, "concept")
    except NotFoundError:
        raise not_found() from None


@router.put("/stories/{story_id}/artifacts/{kind}", response_model=ArtifactResponse)
def update_blueprint_artifact(
    story_id: str, kind: str, payload: BlueprintArtifactUpdate, service: ProjectService = Depends(get_service)
) -> ArtifactResponse:
    try:
        return service.update_blueprint_artifact(story_id, kind, **payload.model_dump())
    except NotFoundError:
        raise not_found() from None
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail={"code": "invalid_artifact_layer"}) from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "version_or_state_conflict"}) from None


@router.get("/stories/{story_id}/artifacts/{kind}", response_model=ArtifactResponse)
def get_blueprint_artifact(story_id: str, kind: str, service: ProjectService = Depends(get_service)) -> ArtifactResponse:
    if kind not in {"bible", "arc", "living_state"}:
        raise not_found()
    try:
        return service.get_artifact(story_id, kind)
    except NotFoundError:
        raise not_found() from None


@router.post("/stories/{story_id}/blueprint/confirm", response_model=StoryResponse)
def confirm_blueprint(story_id: str, service: ProjectService = Depends(get_service)) -> StoryResponse:
    try:
        return service.confirm_blueprint(story_id)
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "blueprint_not_ready"}) from None


@router.post("/stories/{story_id}/chapter-plan", response_model=list[ChapterCard], status_code=status.HTTP_201_CREATED)
def generate_chapter_plan(
    story_id: str,
    payload: ChapterPlanGenerate,
    service: ChapterPlanningService = Depends(get_planning_service),
) -> list[ChapterCard]:
    try:
        return service.generate_plan(story_id, payload.provider, payload.chapter_count)
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "chapter_plan_not_available"}) from None


@router.get("/stories/{story_id}/chapters", response_model=list[ChapterCard])
def list_chapters(story_id: str, service: ChapterPlanningService = Depends(get_planning_service)) -> list[ChapterCard]:
    try:
        return service.list_chapters(story_id)
    except NotFoundError:
        raise not_found() from None


@router.put("/chapters/{chapter_id}/outline", response_model=ChapterCard)
def update_chapter_outline(
    chapter_id: str,
    payload: ChapterOutlineUpdate,
    service: ChapterPlanningService = Depends(get_planning_service),
) -> ChapterCard:
    try:
        return service.update_outline(chapter_id, **payload.model_dump())
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "chapter_outline_conflict"}) from None


@router.get("/chapters/{chapter_id}/workspace", response_model=ChapterWorkspaceResponse)
def get_chapter_workspace(
    chapter_id: str,
    service: ChapterPlanningService = Depends(get_planning_service),
) -> ChapterWorkspaceResponse:
    try:
        chapter = service.assert_active(chapter_id)
        return ChapterWorkspaceResponse(
            chapter=chapter,
            message="当前章节已激活。Chapter Context、Events、Scene 与 Beat 计划将在此工作台中按顺序构建。",
        )
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "chapter_not_active"}) from None


@router.post("/stories/{story_id}/entities", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
def create_entity(story_id: str, payload: EntityCreate, service: ProjectService = Depends(get_service)) -> EntityResponse:
    try:
        return service.create_entity(story_id, entity_type=payload.type, **payload.model_dump(exclude={"type"}))
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "duplicate_entity"}) from None


@router.put("/stories/{story_id}/entities/{entity_id}", response_model=EntityResponse)
def update_entity(
    story_id: str, entity_id: str, payload: EntityUpdate, service: ProjectService = Depends(get_service)
) -> EntityResponse:
    try:
        return service.update_entity(story_id, entity_id, **payload.model_dump())
    except NotFoundError:
        raise not_found() from None
    except ConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "version_or_lock_conflict"}) from None


@router.post("/stories/{story_id}/state-entries", response_model=StateEntryResponse, status_code=status.HTTP_201_CREATED)
def create_state_entry(
    story_id: str, payload: StateEntryCreate, service: ProjectService = Depends(get_service)
) -> StateEntryResponse:
    try:
        return service.create_state_entry(story_id, **payload.model_dump())
    except NotFoundError:
        raise not_found() from None


@router.get("/stories/{story_id}/state-entries", response_model=StateEntriesResponse)
def list_state_entries(story_id: str, service: ProjectService = Depends(get_service)) -> StateEntriesResponse:
    try:
        return service.list_state_entries(story_id)
    except NotFoundError:
        raise not_found() from None
