"""Initial migration for message_records table.

Revision ID: 0001_init
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create message_records table
    op.create_table(
        'message_records',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('message_id', sa.String(length=200), nullable=False),
        sa.Column('channel_type', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('account', sa.String(length=200), nullable=False),
        sa.Column('uid', sa.String(length=100), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_message_records_message_id', 'message_records', ['message_id'], unique=False)
    op.create_index('ix_message_records_channel_type', 'message_records', ['channel_type'], unique=False)
    op.create_index('ix_message_records_channel_message', 'message_records', ['channel_type', 'message_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_message_records_channel_message', table_name='message_records')
    op.drop_index('ix_message_records_channel_type', table_name='message_records')
    op.drop_index('ix_message_records_message_id', table_name='message_records')
    op.drop_table('message_records')
