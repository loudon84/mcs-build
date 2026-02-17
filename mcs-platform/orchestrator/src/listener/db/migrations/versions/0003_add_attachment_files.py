"""Create attachment_files table (listener DB).

Revision ID: 0003_listener
Revises: 0002_listener
Create Date: 2025-02-12

Table schema matches listener.db.models.AttachmentFile:
fields: id (UUID), message_id, file_path, created_at.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_listener"
down_revision: Union[str, None] = "0002_listener"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attachment_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", sa.String(200), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_attachment_files_message_id", "attachment_files", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_attachment_files_message_id", table_name="attachment_files")
    op.drop_table("attachment_files")
