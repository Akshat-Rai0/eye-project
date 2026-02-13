"""add processing_progress column

Revision ID: 7b5d868f1535
Revises: 94412f831b84
Create Date: 2026-02-14 02:34:12.565713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b5d868f1535'
down_revision: Union[str, None] = '94412f831b84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column first
    op.add_column('documents', sa.Column('processing_progress', sa.Integer(), server_default='0', nullable=False))

def downgrade() -> None:
    op.drop_column('documents', 'processing_progress')
