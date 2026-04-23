"""Phone Number Added 

Revision ID: b9afa2edfe20
Revises: 
Create Date: 2026-04-14 21:45:27.385155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9afa2edfe20'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))

def downgrade() -> None:
    #op.drop_column("users", "phone_number")
    pass
