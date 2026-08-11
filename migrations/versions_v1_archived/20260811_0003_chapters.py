"""create phase 3 chapters

Revision ID: 20260811_0003
Revises: 20260810_0002
Create Date: 2026-08-11
"""

from alembic import op
import sqlalchemy as sa

revision = "20260811_0003"
down_revision = "20260810_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stories", sa.Column("active_chapter_ordinal", sa.Integer(), nullable=True))
    op.create_table(
        "chapters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("main_characters", sa.JSON(), nullable=False),
        sa.Column("arc_relation", sa.Text(), nullable=False),
        sa.Column("plan_status", sa.String(length=20), nullable=False),
        sa.Column("access_status", sa.String(length=20), nullable=False),
        sa.Column("stale_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("story_id", "ordinal", name="uq_chapter_story_ordinal"),
    )


def downgrade() -> None:
    op.drop_table("chapters")
    op.drop_column("stories", "active_chapter_ordinal")