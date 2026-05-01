"""add_image_style_note_to_job_posts

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('job_posts') as batch_op:
        batch_op.add_column(sa.Column('image_style_note', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('job_posts') as batch_op:
        batch_op.drop_column('image_style_note')
