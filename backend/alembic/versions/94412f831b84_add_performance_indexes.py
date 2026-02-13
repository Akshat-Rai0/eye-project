"""add performance indexes

Revision ID: 94412f831b84
Revises: d613646f143a
Create Date: 2026-02-14 02:24:04.999521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94412f831b84'
down_revision: Union[str, None] = 'd613646f143a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_documents_created_at', 'documents', ['created_at'], unique=False)
    op.create_index('ix_documents_tags_gin', 'documents', ['tags'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ix_documents_created_at', table_name='documents')
    op.drop_index('ix_documents_tags_gin', table_name='documents')
