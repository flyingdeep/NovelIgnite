"""Phase 6 migration: prose versions, state deltas, consistency issues."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260813_0005_prose_deltas"
down_revision: str | None = "20260813_0004_chapter_workspace"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prose_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), nullable=False),
        sa.Column("scene_id", sa.String(length=36), nullable=False),
        sa.Column("beat_id", sa.String(length=36), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("applied_by", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["beat_id"], ["beats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("beat_id", "version", name="uq_prose_beat_version"),
    )
    op.create_index("ix_prose_versions_beat_id", "prose_versions", ["beat_id"], unique=False)
    op.create_index("ix_prose_versions_chapter_id", "prose_versions", ["chapter_id"], unique=False)
    op.create_index("ix_prose_versions_story_id", "prose_versions", ["story_id"], unique=False)

    op.create_table(
        "state_deltas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("source_version_id", sa.String(length=36), nullable=True),
        sa.Column("changes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("check_result", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_state_deltas_chapter_id", "state_deltas", ["chapter_id"], unique=False)
    op.create_index("ix_state_deltas_story_id", "state_deltas", ["story_id"], unique=False)

    op.create_table(
        "consistency_issues",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("story_id", sa.String(length=36), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), nullable=False),
        sa.Column("checkpoint", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("rule", sa.String(length=120), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consistency_issues_chapter_id", "consistency_issues", ["chapter_id"], unique=False)
    op.create_index("ix_consistency_issues_story_id", "consistency_issues", ["story_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_consistency_issues_story_id", table_name="consistency_issues")
    op.drop_index("ix_consistency_issues_chapter_id", table_name="consistency_issues")
    op.drop_table("consistency_issues")
    op.drop_index("ix_state_deltas_story_id", table_name="state_deltas")
    op.drop_index("ix_state_deltas_chapter_id", table_name="state_deltas")
    op.drop_table("state_deltas")
    op.drop_index("ix_prose_versions_story_id", table_name="prose_versions")
    op.drop_index("ix_prose_versions_chapter_id", table_name="prose_versions")
    op.drop_index("ix_prose_versions_beat_id", table_name="prose_versions")
    op.drop_table("prose_versions")
