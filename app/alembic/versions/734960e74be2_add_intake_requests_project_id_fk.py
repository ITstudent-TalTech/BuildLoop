"""add intake_requests.project_id fk

Revision ID: 734960e74be2
Revises: 20260503_0001
Create Date: 2026-05-06 22:44:36.382474

Promotes project_id from a JSONB-blob key in normalized_input to a
proper nullable FK column on intake_requests.  This replaces the 2.2
workaround that stored {"project_id": str(uuid)} inside normalized_input
to avoid creating a migration at that time.

See DECISIONS.md § "Resolved technical debt".
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "734960e74be2"
down_revision: Union[str, None] = "20260503_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "intake_requests",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_intake_requests_project_id",
        "intake_requests",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_intake_requests_project_id", "intake_requests", type_="foreignkey"
    )
    op.drop_column("intake_requests", "project_id")
