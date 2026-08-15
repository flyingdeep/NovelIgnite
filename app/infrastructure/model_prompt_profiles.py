"""Persistent per-model system prompt profiles and task prompt composition."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.prompts import system_prompt
from app.works.models import ModelPromptProfile


def get_model_prompt_profile(db: Session, provider: str) -> ModelPromptProfile | None:
    return db.get(ModelPromptProfile, provider)


def list_model_prompt_profiles(db: Session, providers: list[str]) -> list[dict]:
    profiles = {profile.provider: profile for profile in db.query(ModelPromptProfile).all()}
    return [
        {
            "provider": provider,
            "system_prompt": profiles.get(provider).system_prompt if provider in profiles else "",
            "version": profiles.get(provider).version if provider in profiles else 0,
            "updated_at": profiles.get(provider).updated_at.isoformat() if provider in profiles else None,
        }
        for provider in providers
    ]


def update_model_prompt_profile(db: Session, provider: str, content: str, expected_version: int | None = None) -> ModelPromptProfile:
    profile = db.get(ModelPromptProfile, provider)
    if profile is None:
        if expected_version not in (None, 0):
            raise ValueError("Model prompt profile version conflict")
        profile = ModelPromptProfile(provider=provider, system_prompt=content.strip(), version=1)
        db.add(profile)
    else:
        if expected_version is not None and profile.version != expected_version:
            raise ValueError("Model prompt profile version conflict")
        profile.system_prompt = content.strip()
        profile.version += 1
        profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


def compose_system_prompt(db: Session, provider: str, action: str) -> str:
    """Stack a user's per-model preset with the immutable task-purpose prompt.

    The model preset is included as an additional system layer, never replacing the
    task prompt. The task prompt is last so required output formats, boundaries and
    task-specific constraints remain authoritative.
    """
    profile = get_model_prompt_profile(db, provider)
    task_prompt = system_prompt(action)
    if profile is None or not profile.system_prompt.strip():
        return task_prompt
    return (
        "【模型预设系统提示词（用户配置，适用于该模型的所有任务）】\n"
        f"{profile.system_prompt.strip()}\n\n"
        "【当前任务系统提示词（必须同时遵守；任务目标、输出格式和边界不可被覆盖）】\n"
        f"{task_prompt}"
    )
