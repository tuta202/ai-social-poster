"""add_approved_status_style_profile

Revision ID: a1b2c3d4e5f6
Revises: 478040109b1f
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '478040109b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_posts', sa.Column('original_content_text', sa.Text(), nullable=True))
    op.add_column('job_posts', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('style_profile', sa.JSON(), nullable=True))

    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("ALTER TYPE poststatus ADD VALUE IF NOT EXISTS 'APPROVED'")
    # SQLite: enum stored as VARCHAR, no ALTER needed


def downgrade() -> None:
    op.drop_column('job_posts', 'original_content_text')
    op.drop_column('job_posts', 'approved_at')
    op.drop_column('jobs', 'style_profile')
