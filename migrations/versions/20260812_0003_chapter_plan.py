"""Phase 4 Chapter Plan migration."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260812_0003_chapter_plan"
down_revision: str | None = "20260811_0002_concept_generation"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chapters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("main_characters", sa.Text(), nullable=False),
        sa.Column("arc_role", sa.String(length=100), nullable=False),
        sa.Column("plan_status", sa.String(length=30), nullable=False),
        sa.Column("access_status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("stale_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("story_id", "ordinal", name="uq_chapters_story_ordinal"),
    )
    op.create_index("ix_chapters_story_id", "chapters", ["story_id"], unique=False)
    op.create_index("ix_chapters_access_status", "chapters", ["access_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chapters_access_status", table_name="chapters")
    op.drop_index("ix_chapters_story_id", table_name="chapters")
    op.drop_table("chapters")
