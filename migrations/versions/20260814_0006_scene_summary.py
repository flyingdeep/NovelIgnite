"""Phase 6 enhancement: scenes.summary column for AI-generated Scene Summary."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260814_0006_scene_summary"
down_revision: str | None = "20260813_0005_prose_deltas"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scenes", sa.Column("summary", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("scenes", "summary")
