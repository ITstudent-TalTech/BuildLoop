"""init core tables

Revision ID: 20260426_0001
Revises: 
Create Date: 2026-04-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260426_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("country_code", sa.Text(), nullable=False, server_default="EE"),
        sa.Column("primary_ehr_code", sa.Text(), nullable=True),
        sa.Column("normalized_address", sa.Text(), nullable=True),
        sa.Column("address_aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("municipality", sa.Text(), nullable=True),
        sa.Column("county", sa.Text(), nullable=True),
        sa.Column("source_identity_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_buildings_primary_ehr_code", "buildings", ["primary_ehr_code"])

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_input_address", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("projects")
    op.drop_index("idx_buildings_primary_ehr_code", table_name="buildings")
    op.drop_table("buildings")
