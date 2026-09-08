"""add inquiry model

Revision ID: f4a8c2d91e03
Revises: 175f9571cf92
Create Date: 2026-09-08 05:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4a8c2d91e03'
down_revision = '175f9571cf92'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'inquiry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('customer_name', sa.String(length=200), nullable=True),
        sa.Column('customer_contact', sa.String(length=200), nullable=True),
        sa.Column('need', sa.Text(), nullable=False),
        sa.Column('fanout_requested', sa.Boolean(), nullable=False),
        sa.Column('fanout_status', sa.String(length=50), nullable=True),
        sa.Column('fanout_reason', sa.String(length=200), nullable=True),
        sa.Column('fanout_provider_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('inquiry')
