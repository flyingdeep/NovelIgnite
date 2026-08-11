"""create phase 1 story tables

Revision ID: 20260810_0001
Revises:
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa

revision = "20260810_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("idea", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "story_artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("layer", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("locked_paths", sa.JSON(), nullable=False),
        sa.Column("source_task_id", sa.String(length=36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("story_id", "kind", "version", name="uq_artifact_story_kind_version"),
    )
    op.create_index("ix_story_artifacts_story_kind", "story_artifacts", ["story_id", "kind"])
    op.create_table(
        "generation_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("input_ref", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("model_snapshot", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failure_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("generation_tasks")
    op.drop_index("ix_story_artifacts_story_kind", table_name="story_artifacts")
    op.drop_table("story_artifacts")
    op.drop_table("stories")
