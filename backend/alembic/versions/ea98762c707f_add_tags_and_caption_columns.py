"""Add tags and caption columns

Revision ID: ea98762c707f
Revises: 
Create Date: 2026-01-05 22:29:24.702341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea98762c707f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if columns exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    # Add tags column if it doesn't exist (using JSON for SQLite compatibility)
    if 'tags' not in columns:
        op.add_column('documents', sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'))
    
    # Add caption column if it doesn't exist
    if 'caption' not in columns:
        op.add_column('documents', sa.Column('caption', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('documents', 'caption')
    op.drop_column('documents', 'tags')
