"""Initial migration for masterdata tables.

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
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('customer_num', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('company_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('customer_id')
    )
    op.create_index('ix_customers_company_id', 'customers', ['company_id'], unique=False)
    op.create_index(op.f('ix_customers_customer_num'), 'customers', ['customer_num'], unique=True)

    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('contact_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('telephone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('contact_id')
    )
    op.create_index('ix_contacts_customer_id', 'contacts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=True)

    # Create companys table
    op.create_table(
        'companys',
        sa.Column('company_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('company_id')
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('product_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('product_id')
    )

    # Create masterdata_versions table
    op.create_table(
        'masterdata_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_masterdata_versions_version'), 'masterdata_versions', ['version'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_masterdata_versions_version'), table_name='masterdata_versions')
    op.drop_table('masterdata_versions')
    op.drop_table('products')
    op.drop_table('companys')
    op.drop_index(op.f('ix_contacts_email'), table_name='contacts')
    op.drop_index('ix_contacts_customer_id', table_name='contacts')
    op.drop_table('contacts')
    op.drop_index(op.f('ix_customers_customer_num'), table_name='customers')
    op.drop_index('ix_customers_company_id', table_name='customers')
    op.drop_table('customers')

