"""Add timestamp fields to CardRequest

Revision ID: a36851639c58
Revises: 3a25581bac99
Create Date: 2023-12-25 01:00:13.424028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a36851639c58'
down_revision: Union[str, None] = '3a25581bac99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('card_requests', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('card_requests', 'created_at')
    # ### end Alembic commands ###
