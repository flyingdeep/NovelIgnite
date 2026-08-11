"""create phase 2 blueprint tables

Revision ID: 20260810_0002
Revises: 20260810_0001
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa

revision = "20260810_0002"
down_revision = "20260810_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("canonical_data", sa.JSON(), nullable=False),
        sa.Column("lock_state", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("story_id", "type", "name", name="uq_entity_story_type_name"),
    )
    op.create_table(
        "state_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("domain", sa.String(length=20), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=True),
        sa.Column("path", sa.String(length=200), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("source_ref", sa.JSON(), nullable=False),
        sa.Column("temporal_scope", sa.JSON(), nullable=False),
        sa.Column("certainty", sa.String(length=20), nullable=False),
        sa.Column("context_policy", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_state_entries_story_domain", "state_entries", ["story_id", "domain"])


def downgrade() -> None:
    op.drop_index("ix_state_entries_story_domain", table_name="state_entries")
    op.drop_table("state_entries")
    op.drop_table("entities")