"""Create message_records table (listener DB).

Revision ID: 0001_listener
Revises:
Create Date: 2025-02-02

Table schema matches listener.db.models.MessageRecord and repo.create_message_record
fields: id, message_id, channel_type, provider, account, uid, from_email,
received_at, processed, processed_at, created_at.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_listener"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_records",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("message_id", sa.String(200), nullable=False),
        sa.Column("channel_type", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("account", sa.String(200), nullable=False),
        sa.Column("uid", sa.String(100), nullable=False),
        sa.Column("from_email", sa.String(500), nullable=False, server_default=""),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_message_records_message_id", "message_records", ["message_id"])
    op.create_index("ix_message_records_channel_type", "message_records", ["channel_type"])
    op.create_index("ix_message_records_channel_message", "message_records", ["channel_type", "message_id"])


def downgrade() -> None:
    op.drop_index("ix_message_records_channel_message", table_name="message_records")
    op.drop_index("ix_message_records_channel_type", table_name="message_records")
    op.drop_index("ix_message_records_message_id", table_name="message_records")
    op.drop_table("message_records")
