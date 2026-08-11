"""Phase 2 schema for Concept artifacts and generation tasks."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260811_0002_concept_generation"
down_revision: str | None = "20260811_0001_phase1_rebuild"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "story_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("layer", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("locked_paths", sa.Text(), nullable=False),
        sa.Column("source_task_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_artifacts_story_id", "story_artifacts", ["story_id"], unique=False)
    op.create_index("ix_story_artifacts_kind", "story_artifacts", ["kind"], unique=False)
    op.create_table(
        "generation_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("model_snapshot", sa.Text(), nullable=False),
        sa.Column("input_ref", sa.Text(), nullable=False),
        sa.Column("output_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_tasks_story_id", "generation_tasks", ["story_id"], unique=False)
    op.create_index("ix_generation_tasks_action", "generation_tasks", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generation_tasks_action", table_name="generation_tasks")
    op.drop_index("ix_generation_tasks_story_id", table_name="generation_tasks")
    op.drop_table("generation_tasks")
    op.drop_index("ix_story_artifacts_kind", table_name="story_artifacts")
    op.drop_index("ix_story_artifacts_story_id", table_name="story_artifacts")
    op.drop_table("story_artifacts")
