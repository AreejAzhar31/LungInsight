"""Add prediction_id to chat_sessions

Revision ID: 7f3a9c1b6e42
Revises: 2de1546de7d8
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.db.types


# revision identifiers, used by Alembic.
revision: str = '7f3a9c1b6e42'
down_revision: Union[str, None] = '2de1546de7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_sessions', sa.Column('prediction_id', app.db.types.GUID(), nullable=True))
    op.create_foreign_key(
        'fk_chat_sessions_prediction_id',
        'chat_sessions', 'predictions',
        ['prediction_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_chat_sessions_prediction_id', 'chat_sessions', type_='foreignkey')
    op.drop_column('chat_sessions', 'prediction_id')
