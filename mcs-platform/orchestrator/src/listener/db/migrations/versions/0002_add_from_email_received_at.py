"""Add from_email and received_at to message_records.

Revision ID: 0002_listener
Revises: 0001_listener
Create Date: 2025-02-02

Adds columns used by repo.create_message_record:
- from_email: message source (email From / wechat from_userid)
- received_at: ISO timestamp from channel; stored as datetime; NULL if missing

Uses IF NOT EXISTS so safe to run when 0001 already created these columns.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_listener"
down_revision: Union[str, None] = "0001_listener"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL: ADD COLUMN IF NOT EXISTS (idempotent when 0001 already has columns)
    op.execute(
        "ALTER TABLE message_records ADD COLUMN IF NOT EXISTS from_email VARCHAR(500) NOT NULL DEFAULT ''"
    )
    op.execute(
        "ALTER TABLE message_records ADD COLUMN IF NOT EXISTS received_at TIMESTAMP NULL"
    )


def downgrade() -> None:
    op.drop_column("message_records", "received_at")
    op.drop_column("message_records", "from_email")
