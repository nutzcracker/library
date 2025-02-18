"""add hashed_password to reader

Revision ID: 37faf7a0ac4e
Revises: 8c84f5e64f1e
Create Date: 2025-01-19 10:17:59.974178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37faf7a0ac4e'
down_revision: Union[str, None] = '8c84f5e64f1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('readers', sa.Column('hashed_password', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('readers', 'hashed_password')
    # ### end Alembic commands ###
