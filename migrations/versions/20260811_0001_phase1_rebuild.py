"""Phase 1 initial schema: stories and per-story AI configuration."""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260811_0001_phase1_rebuild"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("idea_text", sa.Text(), nullable=False),
        sa.Column("cover_color", sa.String(length=20), nullable=False),
        sa.Column("progress_text", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stories_stage", "stories", ["stage"], unique=False)
    op.create_table(
        "ai_configs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("reasoning_strength", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("story_id"),
    )
    op.create_index("ix_ai_configs_story_id", "ai_configs", ["story_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_configs_story_id", table_name="ai_configs")
    op.drop_table("ai_configs")
    op.drop_index("ix_stories_stage", table_name="stories")
    op.drop_table("stories")
