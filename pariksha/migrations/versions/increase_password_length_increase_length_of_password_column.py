"""Increase length of password column

Revision ID: increase_password_length
Revises: 13e819aa29ae
Create Date: 2024-03-30 17:44:18.182973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'increase_password_length'
down_revision = '13e819aa29ae'
branch_labels = None
depends_on = None


def upgrade():
    # Modify the length of the 'password' column to 255 characters
    op.alter_column('user', 'password', type_=sa.String(length=255))


def downgrade():
    # Downgrade is not necessary for this migration
    pass
