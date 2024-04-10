"""Increase length of title column

Revision ID: increase_title_length
Revises: increase_password_length
Create Date: 2024-03-30 17:50:32.032920

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'increase_title_length'
down_revision = 'increase_password_length'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('quiz', 'title', type_=sa.String(length=255))
    pass


def downgrade():
    pass
