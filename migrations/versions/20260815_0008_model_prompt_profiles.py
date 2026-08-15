"""Add persistent per-model system prompt profiles."""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260815_0008_model_prompt_profiles"
down_revision: str | None = "20260814_0007_generation_task_prompt_version"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_prompt_profiles",
        sa.Column("provider", sa.String(length=50), primary_key=True),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("model_prompt_profiles")