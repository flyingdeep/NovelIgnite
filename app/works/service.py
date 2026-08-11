"""Works application service."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.works.models import AIConfig, Story
from app.works.schemas import AIConfigUpdate, IdeaUpdate, WorkCreate


def list_stories(db: Session) -> list[Story]:
    return list(db.scalars(select(Story).where(Story.deleted_at.is_(None)).order_by(Story.updated_at.desc())))


def get_story_or_404(db: Session, story_id: str) -> Story:
    story = db.scalar(select(Story).where(Story.id == story_id, Story.deleted_at.is_(None)))
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


def create_story(db: Session, data: WorkCreate) -> Story:
    story = Story(title=data.title)
    db.add(story)
    db.flush()
    db.add(AIConfig(story_id=story.id))
    db.commit()
    db.refresh(story)
    return story


def soft_delete_story(db: Session, story_id: str) -> None:
    story = get_story_or_404(db, story_id)
    story.deleted_at = story.updated_at = datetime.now(timezone.utc)
    story.version += 1
    db.commit()


def update_idea(db: Session, story_id: str, data: IdeaUpdate) -> Story:
    story = get_story_or_404(db, story_id)
    if story.stage != "idea":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idea is locked after concept generation")
    if story.version != data.expected_version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Story version conflict")
    story.idea_text = data.idea_text
    story.version += 1
    db.commit()
    db.refresh(story)
    return story


def get_ai_config(db: Session, story_id: str) -> AIConfig:
    story = get_story_or_404(db, story_id)
    config = story.ai_config
    if config is None:
        config = AIConfig(story_id=story.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_ai_config(db: Session, story_id: str, data: AIConfigUpdate) -> AIConfig:
    config = get_ai_config(db, story_id)
    if config.version != data.expected_version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="AI config version conflict")
    config.model = data.model
    config.temperature = data.temperature
    config.reasoning_strength = data.reasoning_strength
    config.version += 1
    db.commit()
    db.refresh(config)
    return config
