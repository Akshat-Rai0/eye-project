"""Add content_hash column for duplicate detection

Revision ID: d613646f143a
Revises: ea98762c707f
Create Date: 2026-01-05 22:34:11.814814

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd613646f143a'
down_revision: Union[str, None] = 'ea98762c707f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    if 'content_hash' not in columns:
        # Add content_hash column (nullable for existing records)
        op.add_column('documents', sa.Column('content_hash', sa.String(), nullable=True))
        
        # Create unique index on content_hash for fast duplicate lookups
        # Note: Both SQLite and PostgreSQL allow multiple NULLs in unique index
        op.create_index('ix_documents_content_hash', 'documents', ['content_hash'], unique=True)


def downgrade() -> None:
    # Remove the index and column
    op.drop_index('ix_documents_content_hash', table_name='documents')
    op.drop_column('documents', 'content_hash')
