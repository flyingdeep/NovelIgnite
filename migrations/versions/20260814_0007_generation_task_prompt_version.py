"""Phase 6 enhancement: generation_tasks.prompt_version for prompt version tracking."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260814_0007_generation_task_prompt_version"
down_revision: str | None = "20260814_0006_scene_summary"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generation_tasks", sa.Column("prompt_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("generation_tasks", "prompt_version")
