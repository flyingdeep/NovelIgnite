"""Phase 5 Chapter Workspace migration: snapshots, events, scenes, beats."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260813_0004_chapter_workspace"
down_revision: str | None = "20260812_0003_chapter_plan"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "state_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), nullable=False),
        sa.Column("based_on_chapter_id", sa.String(length=36), nullable=True),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_state_snapshots_chapter_id", "state_snapshots", ["chapter_id"], unique=True)

    op.create_table(
        "chapter_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("related_characters", sa.Text(), nullable=False),
        sa.Column("related_locations", sa.Text(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("planned_result", sa.Text(), nullable=False),
        sa.Column("actual_result", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("arc_role", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chapter_id", "ordinal", name="uq_events_chapter_ordinal"),
    )
    op.create_index("ix_chapter_events_chapter_id", "chapter_events", ["chapter_id"], unique=False)

    op.create_table(
        "scenes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chapter_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("time", sa.String(length=100), nullable=False),
        sa.Column("pov", sa.String(length=100), nullable=False),
        sa.Column("character_goals", sa.Text(), nullable=False),
        sa.Column("conflict", sa.Text(), nullable=False),
        sa.Column("key_events", sa.Text(), nullable=False),
        sa.Column("scene_result", sa.Text(), nullable=False),
        sa.Column("chapter_goal_relation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chapter_id", "ordinal", name="uq_scenes_chapter_ordinal"),
    )
    op.create_index("ix_scenes_chapter_id", "scenes", ["chapter_id"], unique=False)

    op.create_table(
        "beats",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scene_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scene_id", "ordinal", name="uq_beats_scene_ordinal"),
    )
    op.create_index("ix_beats_scene_id", "beats", ["scene_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_beats_scene_id", table_name="beats")
    op.drop_table("beats")
    op.drop_index("ix_scenes_chapter_id", table_name="scenes")
    op.drop_table("scenes")
    op.drop_index("ix_chapter_events_chapter_id", table_name="chapter_events")
    op.drop_table("chapter_events")
    op.drop_index("ix_state_snapshots_chapter_id", table_name="state_snapshots")
    op.drop_table("state_snapshots")
