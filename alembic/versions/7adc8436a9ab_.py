"""empty message

Revision ID: 7adc8436a9ab
Revises: 83f91edfa3b8
Create Date: 2023-12-24 12:21:59.075560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7adc8436a9ab'
down_revision: Union[str, None] = '83f91edfa3b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        table_name='users',
        column_name='telegram_id',
        nullable=False,
        autoincrement=False,
        type_=postgresql.BIGINT()
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.alter_column(
        table_name='users',
        column_name='telegram_id',
        nullable=False,
        autoincrement=False,
        type_=postgresql.INTEGER()
    )
