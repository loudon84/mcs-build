"""Initial migration for orchestrator tables.

Revision ID: 0001_init
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create orchestration_runs table
    op.create_table(
        'orchestration_runs',
        sa.Column('run_id', sa.String(length=100), nullable=False),
        sa.Column('message_id', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('state_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('errors_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('warnings_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('run_id')
    )
    op.create_index('ix_orchestration_runs_message_id', 'orchestration_runs', ['message_id'], unique=False)

    # Create idempotency_records table
    op.create_table(
        'idempotency_records',
        sa.Column('idempotency_key', sa.String(length=200), nullable=False),
        sa.Column('message_id', sa.String(length=200), nullable=False),
        sa.Column('file_sha256', sa.String(length=64), nullable=True),
        sa.Column('customer_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('sales_order_no', sa.String(length=100), nullable=True),
        sa.Column('order_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('idempotency_key')
    )

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', sa.String(length=100), nullable=False),
        sa.Column('step', sa.String(length=100), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_events_run_id', 'audit_events', ['run_id'], unique=False)


def downgrade() -> None:
    # Drop tables (indexes will be automatically dropped with tables in PostgreSQL)
    # In PostgreSQL, dropping a table automatically drops all its indexes,
    # so we don't need to drop indexes explicitly
    # Use IF EXISTS to handle cases where tables may have been partially dropped
    op.execute('DROP TABLE IF EXISTS audit_events')
    op.execute('DROP TABLE IF EXISTS idempotency_records')
    op.execute('DROP TABLE IF EXISTS orchestration_runs')

